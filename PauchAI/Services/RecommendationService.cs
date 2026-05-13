using System.Text;
using System.Text.Json;
using OpenAI.Chat;
using PauchAI.Models;

namespace PauchAI.Services;

public class RecommendationService(IConfiguration config)
{
    private static readonly JsonSerializerOptions _json = new() { PropertyNameCaseInsensitive = true };

    public async Task<RecommendationResponse> RecommendAsync(string userQuery, List<SearchResult> results)
    {
        var apiKey = config["OpenAI:ApiKey"] ?? "";
        var model  = config["OpenAI:Model"] ?? "gpt-4o-mini";

        if (string.IsNullOrWhiteSpace(apiKey) || apiKey == "YOUR_OPENAI_API_KEY_HERE")
            throw new InvalidOperationException("OpenAI API key not configured. Add it to appsettings.Development.json under OpenAI:ApiKey.");

        var client = new ChatClient(model, apiKey);

        var resultsText = new StringBuilder();
        for (int i = 0; i < results.Count; i++)
        {
            var r = results[i];
            resultsText.AppendLine($"[{i + 1}] ID:{r.Id} | {r.ItemName} ({r.ItemCategory})");
            resultsText.AppendLine($"     Type:{r.PouchType} | Material:{r.MaterialType} | Size:{r.Width}×{r.Height}cm Gusset:{r.Gusset}cm");
            resultsText.AppendLine($"     Thickness:{r.Thickness}µm | Print:{r.PrintingType} | ZipLock:{r.ZipLock} | FoodGrade:{r.FoodGrade}");
            resultsText.AppendLine($"     Qty:{r.Quantity} | ShelfLife:{r.ShelfLifeMonths}mo | CostPerPouch:₹{r.CostPerPouch:N4}");
            resultsText.AppendLine($"     Match:{r.Similarity * 100:N0}% | Description:{r.Description}");
            resultsText.AppendLine();
        }

        var systemPrompt = """
            You are a packaging expert who recommends flexible pouches to customers.
            You will be given a customer requirement and a list of semantically matched pouch options.
            Select the best 1-3 pouches from the list and explain clearly why each is a good fit.
            Be specific about the features that match the requirement.
            Respond ONLY with valid JSON in this exact format:
            {
              "summary": "one sentence overall recommendation summary",
              "recommendations": [
                {
                  "rank": 1,
                  "id": <pouch_id_integer>,
                  "reasoning": "clear explanation of why this pouch fits the requirement"
                }
              ]
            }
            """;

        var userPrompt = $"""
            Customer requirement: "{userQuery}"

            Available pouch options (from semantic search):
            {resultsText}

            Recommend the best 1-3 pouches from the list above. Do not suggest pouches not in the list.
            """;

        var chatMessages = new List<ChatMessage>
        {
            new SystemChatMessage(systemPrompt),
            new UserChatMessage(userPrompt)
        };

        var completion = await client.CompleteChatAsync(chatMessages);
        var raw = completion.Value.Content[0].Text.Trim();

        // Strip markdown code fences if present
        if (raw.StartsWith("```"))
        {
            raw = raw.Split('\n').Skip(1).ToList() is { } lines
                ? string.Join('\n', lines.Take(lines.Count - 1))
                : raw;
            raw = raw.TrimEnd('`').Trim();
        }

        using var doc = JsonDocument.Parse(raw);
        var root = doc.RootElement;

        var summary = root.TryGetProperty("summary", out var s) ? s.GetString() ?? "" : "";
        var recs    = new List<PouchRecommendation>();

        if (root.TryGetProperty("recommendations", out var recsEl))
        {
            foreach (var rec in recsEl.EnumerateArray())
            {
                var id        = rec.TryGetProperty("id",        out var idEl)  ? idEl.GetInt32()        : 0;
                var rank      = rec.TryGetProperty("rank",      out var rkEl)  ? rkEl.GetInt32()        : recs.Count + 1;
                var reasoning = rec.TryGetProperty("reasoning", out var rsEl)  ? rsEl.GetString() ?? "" : "";

                var matched = results.FirstOrDefault(r => r.Id == id);
                if (matched is not null)
                    recs.Add(new PouchRecommendation { Rank = rank, Pouch = matched, Reasoning = reasoning });
            }
        }

        return new RecommendationResponse { Summary = summary, Recommendations = recs };
    }
}

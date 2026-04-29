using System.Net.Http.Json;
using PauchAI.Models;

namespace PauchAI.Services;

public class PouchPredictionService(HttpClient http)
{
    public async Task<List<SearchResult>> SearchAsync(SearchQuery query)
    {
        var response = await http.PostAsJsonAsync("search", query);
        if (!response.IsSuccessStatusCode)
        {
            var body = await response.Content.ReadAsStringAsync();
            throw new InvalidOperationException($"Search service returned {(int)response.StatusCode}: {body}");
        }
        return await response.Content.ReadFromJsonAsync<List<SearchResult>>()
            ?? [];
    }

    public async Task<PredictionResult> PredictAsync(PouchInput input)
    {
        var response = await http.PostAsJsonAsync("predict", input);
        if (!response.IsSuccessStatusCode)
        {
            var body = await response.Content.ReadAsStringAsync();
            throw new InvalidOperationException($"Prediction service returned {(int)response.StatusCode}: {body}");
        }
        return await response.Content.ReadFromJsonAsync<PredictionResult>()
            ?? throw new InvalidOperationException("Empty response from prediction service.");
    }

    public async Task<List<BatchPredictionRow>> PredictBatchAsync(List<PouchInput> inputs)
    {
        var response = await http.PostAsJsonAsync("predict/batch", inputs);
        if (!response.IsSuccessStatusCode)
        {
            var body = await response.Content.ReadAsStringAsync();
            throw new InvalidOperationException($"Prediction service returned {(int)response.StatusCode}: {body}");
        }

        var items = await response.Content.ReadFromJsonAsync<List<BatchPredictionItem>>()
            ?? throw new InvalidOperationException("Empty batch response from prediction service.");

        return items.Select((item, i) => new BatchPredictionRow
        {
            RowNumber            = item.Row,
            Input                = inputs[i],
            PredictedCostPerPouch = item.PredictedCostPerPouch,
            TotalEstimatedCost   = item.TotalEstimatedCost,
        }).ToList();
    }
}

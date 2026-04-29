using System.Text.Json.Serialization;

namespace PauchAI.Models;

public class PredictionResult
{
    [JsonPropertyName("predicted_cost_per_pouch")]
    public double PredictedCostPerPouch { get; set; }

    [JsonPropertyName("total_estimated_cost")]
    public double TotalEstimatedCost { get; set; }

    [JsonPropertyName("currency")]
    public string Currency { get; set; } = "INR";
}

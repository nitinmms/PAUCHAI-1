using System.Text.Json.Serialization;

namespace PauchAI.Models;

public class BatchPredictionRow
{
    public int RowNumber { get; set; }
    public PouchInput Input { get; set; } = new();
    public double PredictedCostPerPouch { get; set; }
    public double TotalEstimatedCost { get; set; }
}

public class BatchPredictionItem
{
    [JsonPropertyName("row")]
    public int Row { get; set; }

    [JsonPropertyName("predicted_cost_per_pouch")]
    public double PredictedCostPerPouch { get; set; }

    [JsonPropertyName("total_estimated_cost")]
    public double TotalEstimatedCost { get; set; }
}

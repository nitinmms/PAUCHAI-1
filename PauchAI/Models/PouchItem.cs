namespace PauchAI.Models;

public class PouchItem
{
    public long Id { get; set; }
    public string? ItemName { get; set; }
    public string? ItemCategory { get; set; }
    public decimal? ProductWeightG { get; set; }
    public string? PouchType { get; set; }
    public string? MaterialType { get; set; }
    public decimal? WidthCm { get; set; }
    public decimal? HeightCm { get; set; }
    public decimal? GussetCm { get; set; }
    public decimal? ThicknessMicron { get; set; }
    public string? PrintingType { get; set; }
    public bool ZipLock { get; set; }
    public int? Quantity { get; set; }
    public decimal? MaterialCostPerKg { get; set; }
    public decimal? EstimatedCostPerPouch { get; set; }
    public decimal? ActualCostPerPouch { get; set; }
    public string? SemanticDescription { get; set; }
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
}

using System.Text.Json.Serialization;

namespace PauchAI.Models;

public class SearchQuery
{
    [JsonPropertyName("query")]
    public string Query { get; set; } = "";

    [JsonPropertyName("limit")]
    public int Limit { get; set; } = 5;

    [JsonPropertyName("food_safe_only")]
    public bool FoodSafeOnly { get; set; }

    [JsonPropertyName("material_type")]
    public string? MaterialType { get; set; }

    [JsonPropertyName("zip_lock")]
    public string? ZipLock { get; set; }
}

public class SearchResult
{
    [JsonPropertyName("id")]
    public int Id { get; set; }

    [JsonPropertyName("item_name")]
    public string ItemName { get; set; } = "";

    [JsonPropertyName("item_category")]
    public string ItemCategory { get; set; } = "";

    [JsonPropertyName("description")]
    public string Description { get; set; } = "";

    [JsonPropertyName("similarity")]
    public double Similarity { get; set; }

    [JsonPropertyName("width")]
    public double Width { get; set; }

    [JsonPropertyName("height")]
    public double Height { get; set; }

    [JsonPropertyName("gusset")]
    public double Gusset { get; set; }

    [JsonPropertyName("material_type")]
    public string MaterialType { get; set; } = "";

    [JsonPropertyName("thickness")]
    public int Thickness { get; set; }

    [JsonPropertyName("printing_type")]
    public string PrintingType { get; set; } = "";

    [JsonPropertyName("pouch_type")]
    public string PouchType { get; set; } = "";

    [JsonPropertyName("zip_lock")]
    public string ZipLock { get; set; } = "";

    [JsonPropertyName("food_grade")]
    public string FoodGrade { get; set; } = "no";

    [JsonPropertyName("barrier_level")]
    public string BarrierLevel { get; set; } = "";

    [JsonPropertyName("shelf_life_months")]
    public int ShelfLifeMonths { get; set; }

    [JsonPropertyName("quantity")]
    public int Quantity { get; set; }

    [JsonPropertyName("cost_per_pouch")]
    public double CostPerPouch { get; set; }

    public string CostPredictorUrl =>
        $"/pouch-cost?width={Width}&height={Height}&gusset={Gusset}" +
        $"&materialType={Uri.EscapeDataString(NormalizeMaterial(MaterialType))}" +
        $"&thickness={Thickness}" +
        $"&printingType={Uri.EscapeDataString(NormalizePrinting(PrintingType))}" +
        $"&pouchType={Uri.EscapeDataString(NormalizePouchType(PouchType))}" +
        $"&zipLock={Uri.EscapeDataString(ZipLock)}";

    private static string NormalizePrinting(string v) => v.ToLowerInvariant().Trim() switch
    {
        "flexo" or "flexographic"                       => "flexo",
        "rotogravure" or "gravure" or "full color"
            or "full colour" or "digital"               => "rotogravure",
        _                                               => "none",
    };

    private static string NormalizePouchType(string v) => v.ToLowerInvariant().Trim() switch
    {
        "3-side-seal" or "3-side seal" or "3 side seal"
            or "three side seal"                        => "3-side-seal",
        "stand-up" or "stand up" or "standup"
            or "doypack" or "doy pack"                  => "stand-up",
        "center-seal" or "center seal" or "centre seal"
            or "back seal" or "fin seal"                => "center-seal",
        _                                               => "3-side-seal",
    };

    private static string NormalizeMaterial(string v) => v.ToUpperInvariant().Trim() switch
    {
        "PET+PE" or "PETPE"                             => "PET+PE",
        "BOPP+CPP" or "BOPPCPP"
            or "MET BOPP+CPP" or "METBOPP+CPP"         => "BOPP+CPP",
        "PAPER" or "KRAFT+PE" or "KRAFT PE"             => "Paper",
        "FOIL" or "PET+ALU+PE" or "ALU"
            or "ALUMINIUM" or "ALUMINUM"                => "Foil",
        _                                               => "PET+PE",
    };
}

namespace PauchAI.Models;

public class PouchRecommendation
{
    public int Rank { get; set; }
    public SearchResult Pouch { get; set; } = new();
    public string Reasoning { get; set; } = "";
}

public class RecommendationResponse
{
    public List<PouchRecommendation> Recommendations { get; set; } = [];
    public string Summary { get; set; } = "";
}

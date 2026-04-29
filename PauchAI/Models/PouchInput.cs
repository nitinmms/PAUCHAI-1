using System.ComponentModel.DataAnnotations;
using System.Text.Json.Serialization;

namespace PauchAI.Models;

public class PouchInput
{
    [Required, Range(1, 200, ErrorMessage = "Width must be between 1 and 200 cm")]
    [JsonPropertyName("width")]
    public double Width { get; set; } = 15;

    [Required, Range(1, 200, ErrorMessage = "Height must be between 1 and 200 cm")]
    [JsonPropertyName("height")]
    public double Height { get; set; } = 22;

    [Range(0, 50)]
    [JsonPropertyName("gusset")]
    public double Gusset { get; set; } = 0;

    [Required(ErrorMessage = "Please select a material type.")]
    [JsonPropertyName("material_type")]
    public string MaterialType { get; set; } = "PET+PE";

    [Required, Range(10, 500, ErrorMessage = "Thickness must be between 10 and 500 microns")]
    [JsonPropertyName("thickness")]
    public double Thickness { get; set; } = 100;

    [Required]
    [JsonPropertyName("printing_type")]
    public string PrintingType { get; set; } = "none";

    [Required, Range(100, 10_000_000, ErrorMessage = "Quantity must be at least 100")]
    [JsonPropertyName("quantity")]
    public int Quantity { get; set; } = 10000;

    [Required]
    [JsonPropertyName("pouch_type")]
    public string PouchType { get; set; } = "3-side-seal";

    [JsonPropertyName("zip_lock")]
    public string ZipLock { get; set; } = "no";
}

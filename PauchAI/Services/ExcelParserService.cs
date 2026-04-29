using ClosedXML.Excel;
using PauchAI.Models;

namespace PauchAI.Services;

public class ExcelParserService
{
    private static readonly Dictionary<string, string[]> ColumnKeywords = new()
    {
        ["width"]         = ["width", "w(cm)", "w_cm"],
        ["height"]        = ["height", "h(cm)", "h_cm", "length"],
        ["gusset"]        = ["gusset", "g(cm)", "g_cm", "depth"],
        ["material_type"] = ["material", "mat"],
        ["thickness"]     = ["thickness", "thick", "micron"],
        ["printing_type"] = ["print"],
        ["quantity"]      = ["quantity", "qty", "pieces", "pcs", "nos"],
        ["pouch_type"]    = ["pouch", "type", "style"],
        ["zip_lock"]      = ["zip", "lock", "reseal", "zipper"],
    };

    public (List<PouchInput> Rows, List<string> Errors) Parse(Stream stream)
    {
        var rows   = new List<PouchInput>();
        var errors = new List<string>();

        using var wb = new XLWorkbook(stream);
        var ws = wb.Worksheet(1);

        var usedRows = ws.RowsUsed().ToList();
        if (usedRows.Count < 2)
        {
            errors.Add("The Excel file must have at least one header row and one data row.");
            return (rows, errors);
        }

        // Map column letter → field name
        var colMap = new Dictionary<int, string>();
        foreach (var cell in usedRows[0].CellsUsed())
        {
            var header = cell.GetString().ToLower().Trim();
            foreach (var (field, keywords) in ColumnKeywords)
            {
                if (keywords.Any(kw => header.Contains(kw)))
                {
                    colMap[cell.Address.ColumnNumber] = field;
                    break;
                }
            }
        }

        var missing = ColumnKeywords.Keys.Except(colMap.Values).ToList();
        if (missing.Any())
        {
            errors.Add($"Could not find columns: {string.Join(", ", missing)}. " +
                       "Check that your Excel headers match the expected names.");
            return (rows, errors);
        }

        foreach (var row in usedRows.Skip(1))
        {
            var rowNum = row.RowNumber();
            try
            {
                string Get(string field)
                {
                    var col = colMap.First(kv => kv.Value == field).Key;
                    return row.Cell(col).GetString().Trim();
                }

                var input = new PouchInput
                {
                    Width        = ParseDouble(Get("width"),         rowNum, "width",         errors),
                    Height       = ParseDouble(Get("height"),        rowNum, "height",        errors),
                    Gusset       = ParseDoubleOpt(Get("gusset")),
                    MaterialType = NormalizeMaterial(Get("material_type")),
                    Thickness    = ParseDouble(Get("thickness"),     rowNum, "thickness",     errors),
                    PrintingType = NormalizePrinting(Get("printing_type")),
                    Quantity     = (int)ParseDouble(Get("quantity"), rowNum, "quantity",      errors),
                    PouchType    = NormalizePouchType(Get("pouch_type")),
                    ZipLock      = NormalizeZipLock(Get("zip_lock")),
                };
                rows.Add(input);
            }
            catch
            {
                errors.Add($"Row {rowNum}: skipped due to unexpected data.");
            }
        }

        return (rows, errors);
    }

    // ── Normalizers ──────────────────────────────────────────────────────────

    private static string NormalizeMaterial(string v)
    {
        var s = v.ToUpper();
        if (s.Contains("FOIL") || s.Contains("AL") || s.Contains("ALUM")) return "Foil";
        if (s.Contains("PET"))  return "PET+PE";
        if (s.Contains("BOPP")) return "BOPP+CPP";
        if (s.Contains("PAPER") || s.Contains("KRAFT")) return "Paper";
        return "PET+PE";
    }

    private static string NormalizePrinting(string v)
    {
        var s = v.ToLower();
        if (s.Contains("roto") || s.Contains("gravure")) return "rotogravure";
        if (s.Contains("flexo")) return "flexo";
        return "none";
    }

    private static string NormalizePouchType(string v)
    {
        var s = v.ToLower();
        if (s.Contains("stand") || s.Contains("doy")) return "stand-up";
        if (s.Contains("center") || s.Contains("back")) return "center-seal";
        return "3-side-seal";
    }

    private static string NormalizeZipLock(string v)
    {
        var s = v.ToLower().Trim();
        return s is "yes" or "y" or "1" or "true" ? "yes" : "no";
    }

    // ── Parsers ───────────────────────────────────────────────────────────────

    private static double ParseDouble(string v, int row, string field, List<string> errors)
    {
        if (double.TryParse(v, out var d)) return d;
        errors.Add($"Row {row}: cannot parse '{field}' value '{v}' as a number — defaulting to 0.");
        return 0;
    }

    private static double ParseDoubleOpt(string v)
        => double.TryParse(v, out var d) ? d : 0;
}

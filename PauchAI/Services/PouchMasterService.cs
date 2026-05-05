using Npgsql;
using PauchAI.Models;

namespace PauchAI.Services;

public class PouchMasterService(IConfiguration config)
{
    private NpgsqlConnection Connect() =>
        new(config.GetConnectionString("PostgreSQL"));

    public async Task<List<PouchItem>> GetAllAsync()
    {
        var list = new List<PouchItem>();
        await using var conn = Connect();
        await conn.OpenAsync();
        await using var cmd = new NpgsqlCommand(
            "SELECT id, item_name, item_category, product_weight_g, pouch_type, material_type, " +
            "width_cm, height_cm, gusset_cm, thickness_micron, printing_type, zip_lock, quantity, " +
            "material_cost_per_kg, estimated_cost_per_pouch, actual_cost_per_pouch, " +
            "semantic_description, created_at " +
            "FROM public.pouch_items ORDER BY id DESC", conn);
        await using var reader = await cmd.ExecuteReaderAsync();
        while (await reader.ReadAsync())
            list.Add(Map(reader));
        return list;
    }

    public async Task<PouchItem?> GetByIdAsync(long id)
    {
        await using var conn = Connect();
        await conn.OpenAsync();
        await using var cmd = new NpgsqlCommand(
            "SELECT id, item_name, item_category, product_weight_g, pouch_type, material_type, " +
            "width_cm, height_cm, gusset_cm, thickness_micron, printing_type, zip_lock, quantity, " +
            "material_cost_per_kg, estimated_cost_per_pouch, actual_cost_per_pouch, " +
            "semantic_description, created_at " +
            "FROM public.pouch_items WHERE id = @id", conn);
        cmd.Parameters.AddWithValue("id", id);
        await using var reader = await cmd.ExecuteReaderAsync();
        return await reader.ReadAsync() ? Map(reader) : null;
    }

    public async Task<long> CreateAsync(PouchItem item)
    {
        await using var conn = Connect();
        await conn.OpenAsync();
        await using var cmd = new NpgsqlCommand(
            "INSERT INTO public.pouch_items " +
            "(item_name, item_category, product_weight_g, pouch_type, material_type, " +
            "width_cm, height_cm, gusset_cm, thickness_micron, printing_type, zip_lock, quantity, " +
            "material_cost_per_kg, estimated_cost_per_pouch, actual_cost_per_pouch, semantic_description) " +
            "VALUES (@name,@cat,@wgt,@ptype,@mtype,@w,@h,@g,@th,@print,@zip,@qty,@mck,@est,@act,@desc) " +
            "RETURNING id", conn);
        AddParams(cmd, item);
        return (long)(await cmd.ExecuteScalarAsync())!;
    }

    public async Task UpdateAsync(PouchItem item)
    {
        await using var conn = Connect();
        await conn.OpenAsync();
        await using var cmd = new NpgsqlCommand(
            "UPDATE public.pouch_items SET " +
            "item_name=@name, item_category=@cat, product_weight_g=@wgt, pouch_type=@ptype, " +
            "material_type=@mtype, width_cm=@w, height_cm=@h, gusset_cm=@g, thickness_micron=@th, " +
            "printing_type=@print, zip_lock=@zip, quantity=@qty, material_cost_per_kg=@mck, " +
            "estimated_cost_per_pouch=@est, actual_cost_per_pouch=@act, semantic_description=@desc " +
            "WHERE id=@id", conn);
        cmd.Parameters.AddWithValue("id", item.Id);
        AddParams(cmd, item);
        await cmd.ExecuteNonQueryAsync();
    }

    public async Task DeleteAsync(long id)
    {
        await using var conn = Connect();
        await conn.OpenAsync();
        await using var cmd = new NpgsqlCommand(
            "DELETE FROM public.pouch_items WHERE id = @id", conn);
        cmd.Parameters.AddWithValue("id", id);
        await cmd.ExecuteNonQueryAsync();
    }

    private static void AddParams(NpgsqlCommand cmd, PouchItem i)
    {
        cmd.Parameters.AddWithValue("name",  (object?)i.ItemName ?? DBNull.Value);
        cmd.Parameters.AddWithValue("cat",   (object?)i.ItemCategory ?? DBNull.Value);
        cmd.Parameters.AddWithValue("wgt",   (object?)i.ProductWeightG ?? DBNull.Value);
        cmd.Parameters.AddWithValue("ptype", (object?)i.PouchType ?? DBNull.Value);
        cmd.Parameters.AddWithValue("mtype", (object?)i.MaterialType ?? DBNull.Value);
        cmd.Parameters.AddWithValue("w",     (object?)i.WidthCm ?? DBNull.Value);
        cmd.Parameters.AddWithValue("h",     (object?)i.HeightCm ?? DBNull.Value);
        cmd.Parameters.AddWithValue("g",     (object?)i.GussetCm ?? DBNull.Value);
        cmd.Parameters.AddWithValue("th",    (object?)i.ThicknessMicron ?? DBNull.Value);
        cmd.Parameters.AddWithValue("print", (object?)i.PrintingType ?? DBNull.Value);
        cmd.Parameters.AddWithValue("zip",   i.ZipLock);
        cmd.Parameters.AddWithValue("qty",   (object?)i.Quantity ?? DBNull.Value);
        cmd.Parameters.AddWithValue("mck",   (object?)i.MaterialCostPerKg ?? DBNull.Value);
        cmd.Parameters.AddWithValue("est",   (object?)i.EstimatedCostPerPouch ?? DBNull.Value);
        cmd.Parameters.AddWithValue("act",   (object?)i.ActualCostPerPouch ?? DBNull.Value);
        cmd.Parameters.AddWithValue("desc",  (object?)i.SemanticDescription ?? DBNull.Value);
    }

    private static PouchItem Map(NpgsqlDataReader r) => new()
    {
        Id                   = r.GetInt64(0),
        ItemName             = r.IsDBNull(1)  ? null : r.GetString(1),
        ItemCategory         = r.IsDBNull(2)  ? null : r.GetString(2),
        ProductWeightG       = r.IsDBNull(3)  ? null : r.GetDecimal(3),
        PouchType            = r.IsDBNull(4)  ? null : r.GetString(4),
        MaterialType         = r.IsDBNull(5)  ? null : r.GetString(5),
        WidthCm              = r.IsDBNull(6)  ? null : r.GetDecimal(6),
        HeightCm             = r.IsDBNull(7)  ? null : r.GetDecimal(7),
        GussetCm             = r.IsDBNull(8)  ? null : r.GetDecimal(8),
        ThicknessMicron      = r.IsDBNull(9)  ? null : r.GetDecimal(9),
        PrintingType         = r.IsDBNull(10) ? null : r.GetString(10),
        ZipLock              = !r.IsDBNull(11) && r.GetBoolean(11),
        Quantity             = r.IsDBNull(12) ? null : r.GetInt32(12),
        MaterialCostPerKg    = r.IsDBNull(13) ? null : r.GetDecimal(13),
        EstimatedCostPerPouch = r.IsDBNull(14) ? null : r.GetDecimal(14),
        ActualCostPerPouch   = r.IsDBNull(15) ? null : r.GetDecimal(15),
        SemanticDescription  = r.IsDBNull(16) ? null : r.GetString(16),
        CreatedAt            = r.GetDateTime(17),
    };
}

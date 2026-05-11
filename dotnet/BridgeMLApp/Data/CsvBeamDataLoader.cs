using BridgeMLApp.Domain;
using Microsoft.ML;
using Microsoft.ML.Data;
using System.Globalization;

namespace BridgeMLApp.Data;

public class CsvBeamDataLoader
{
    private readonly MLContext _mlContext;

    public CsvBeamDataLoader(MLContext mlContext)
    {
        _mlContext = mlContext;
    }

    public IDataView Load(
        string filePath,
        string targetColumn,
        string[] featureColumns)
    {
        if (!File.Exists(filePath))
            throw new FileNotFoundException($"CSV file not found: {filePath}");

        var records = ReadRecords(filePath, targetColumn, featureColumns);

        Console.WriteLine($"Loaded records: {records.Count}");

        var schemaDefinition = SchemaDefinition.Create(typeof(BeamRecord));
        schemaDefinition[nameof(BeamRecord.Features)].ColumnType =
            new VectorDataViewType(NumberDataViewType.Single, featureColumns.Length);

        return _mlContext.Data.LoadFromEnumerable(records, schemaDefinition);
    }

    private static List<BeamRecord> ReadRecords(
        string filePath,
        string targetColumn,
        string[] featureColumns)
    {
        var lines = File.ReadAllLines(filePath);

        if (lines.Length < 2)
            throw new Exception("CSV is empty or contains only header.");

        var headers = lines[0].Split(',');

        var headerIndex = headers
            .Select((name, index) => new { Name = name.Trim(), Index = index })
            .ToDictionary(x => x.Name, x => x.Index);

        if (!headerIndex.ContainsKey(targetColumn))
            throw new Exception($"Target column not found: {targetColumn}");

        foreach (var featureColumn in featureColumns)
        {
            if (!headerIndex.ContainsKey(featureColumn))
                throw new Exception($"Feature column not found: {featureColumn}");
        }

        var records = new List<BeamRecord>();

        foreach (var line in lines.Skip(1))
        {
            if (string.IsNullOrWhiteSpace(line))
                continue;

            var values = line.Split(',');

            if (GetString(values, headerIndex, "analysis_status") != "OK")
                continue;

            var features = featureColumns
                .Select(col => GetFloat(values, headerIndex, col))
                .ToArray();

            var label = GetFloat(values, headerIndex, targetColumn);

            records.Add(new BeamRecord
            {
                Features = features,
                Label = label
            });
        }

        return records;
    }

    private static float GetFloat(
        string[] values,
        Dictionary<string, int> headerIndex,
        string columnName)
    {
        if (!headerIndex.TryGetValue(columnName, out int index))
            throw new Exception($"Column not found: {columnName}");

        if (index >= values.Length)
            return 0f;

        var value = values[index];

        if (string.IsNullOrWhiteSpace(value))
            return 0f;

        return float.Parse(value, CultureInfo.InvariantCulture);
    }

    private static string GetString(
        string[] values,
        Dictionary<string, int> headerIndex,
        string columnName)
    {
        if (!headerIndex.TryGetValue(columnName, out int index))
            return string.Empty;

        if (index >= values.Length)
            return string.Empty;

        return values[index].Trim();
    }
}
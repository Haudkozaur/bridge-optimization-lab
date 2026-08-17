using BridgeMLApp.Domain;
using Microsoft.ML;
using Microsoft.ML.Data;
using System.Globalization;

namespace BridgeMLApp.Data;

public sealed class MultiSpanCsvBeamDataLoader
{
    private readonly MLContext _mlContext;

    public MultiSpanCsvBeamDataLoader(MLContext mlContext)
    {
        _mlContext = mlContext;
    }

    public IReadOnlyList<BeamRecord> LastLoadedRecords { get; private set; } = [];

    public int LastSkippedBecauseStatus { get; private set; }

    public int LastSkippedBecauseTargetMissing { get; private set; }

    public int LastSkippedBecauseFeatureError { get; private set; }

    public IDataView Load(
        string filePath,
        string targetColumn,
        MultiSpanFeatureBuilder featureBuilder)
    {
        if (!File.Exists(filePath))
            throw new FileNotFoundException($"CSV file not found: {filePath}");

        var records = ReadRecords(filePath, targetColumn, featureBuilder);

        LastLoadedRecords = records;

        Console.WriteLine($"Loaded records: {records.Count}");
        Console.WriteLine($"Skipped because analysis_status != OK: {LastSkippedBecauseStatus}");
        Console.WriteLine($"Skipped because target missing/invalid: {LastSkippedBecauseTargetMissing}");
        Console.WriteLine($"Skipped because feature build failed: {LastSkippedBecauseFeatureError}");
        Console.WriteLine($"Feature count: {featureBuilder.FeatureCount}");

        if (records.Count == 0)
            throw new InvalidOperationException($"No records loaded for target: {targetColumn}");

        var schemaDefinition = SchemaDefinition.Create(typeof(BeamRecord));
        schemaDefinition[nameof(BeamRecord.Features)].ColumnType =
            new VectorDataViewType(NumberDataViewType.Single, featureBuilder.FeatureCount);

        return _mlContext.Data.LoadFromEnumerable(records, schemaDefinition);
    }

    private List<BeamRecord> ReadRecords(
        string filePath,
        string targetColumn,
        MultiSpanFeatureBuilder featureBuilder)
    {
        LastSkippedBecauseStatus = 0;
        LastSkippedBecauseTargetMissing = 0;
        LastSkippedBecauseFeatureError = 0;

        var lines = File.ReadAllLines(filePath);

        if (lines.Length < 2)
            throw new Exception("CSV is empty or contains only header.");

        var headers = lines[0].Split(',');

        var headerIndex = headers
            .Select((name, index) => new { Name = name.Trim(), Index = index })
            .ToDictionary(x => x.Name, x => x.Index);

        if (!headerIndex.ContainsKey(targetColumn))
            throw new Exception($"Target column not found: {targetColumn}");

        var records = new List<BeamRecord>();

        foreach (var line in lines.Skip(1))
        {
            if (string.IsNullOrWhiteSpace(line))
                continue;

            var values = line.Split(',');

            var status = GetString(values, headerIndex, "analysis_status");

            if (!string.IsNullOrWhiteSpace(status) &&
                !string.Equals(status, "OK", StringComparison.OrdinalIgnoreCase))
            {
                LastSkippedBecauseStatus++;
                continue;
            }

            if (!TryGetRequiredFloat(values, headerIndex, targetColumn, out var label))
            {
                LastSkippedBecauseTargetMissing++;
                continue;
            }

            float[] features;

            try
            {
                features = featureBuilder.BuildFeatures(values, headerIndex);
            }
            catch
            {
                LastSkippedBecauseFeatureError++;
                continue;
            }

            records.Add(new BeamRecord
            {
                Features = features,
                Label = label
            });
        }

        return records;
    }

    private static bool TryGetRequiredFloat(
        string[] values,
        IReadOnlyDictionary<string, int> headerIndex,
        string columnName,
        out float result)
    {
        result = 0f;

        if (!headerIndex.TryGetValue(columnName, out var index))
            return false;

        if (index < 0 || index >= values.Length)
            return false;

        var raw = values[index];

        if (string.IsNullOrWhiteSpace(raw))
            return false;

        if (!float.TryParse(raw, NumberStyles.Float, CultureInfo.InvariantCulture, out result))
            return false;

        if (float.IsNaN(result) || float.IsInfinity(result))
            return false;

        return true;
    }

    private static string GetString(
        string[] values,
        IReadOnlyDictionary<string, int> headerIndex,
        string columnName)
    {
        if (!headerIndex.TryGetValue(columnName, out int index))
            return string.Empty;

        if (index < 0 || index >= values.Length)
            return string.Empty;

        return values[index].Trim();
    }
}
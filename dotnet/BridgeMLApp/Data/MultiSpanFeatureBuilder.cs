using System.Globalization;

namespace BridgeMLApp.Data;

public sealed class MultiSpanFeatureBuilder
{
    public const int MaxSpans = 10;
    public const int MaxSupports = MaxSpans + 1;
    public const int MaxTendonControlPoints = 4 * MaxSpans + 1;


    public IReadOnlyList<string> FeatureNames { get; } = BuildFeatureNames();

    public int FeatureCount => FeatureNames.Count;

    public float[] BuildFeatures(
        string[] values,
        IReadOnlyDictionary<string, int> headerIndex)
    {
        var features = new List<float>(FeatureCount);

        var spanLengths = ParseFloatList(GetString(values, headerIndex, "span_lengths_m"));
        var beamDivisions = ParseFloatList(GetString(values, headerIndex, "beam_divisions"));
        var tendonEcc = ParseFloatList(GetString(values, headerIndex, "tendon_ecc_control_points_m"));
        var udlValues = ParseFloatList(GetString(values, headerIndex, "udl_values_kn_per_m"));

        var nSpans = GetFloat(
            values,
            headerIndex,
            "n_spans_parsed",
            GetFloat(values, headerIndex, "n_spans"));

        Add(features, nSpans);
        Add(features, GetFloat(values, headerIndex, "total_span_length_m", spanLengths.Sum()));
        Add(features, GetFloat(values, headerIndex, "total_divisions", beamDivisions.Sum()));
        Add(features, GetFloat(values, headerIndex, "tendon_control_points_per_span"));
        Add(features, GetFloat(values, headerIndex, "beam_height_m"));
        Add(features, GetFloat(values, headerIndex, "beam_width_m"));
        Add(features, GetFloat(values, headerIndex, "tendon_cover_m"));
        Add(features, GetFloat(values, headerIndex, "n_tendons"));
        Add(features, GetFloat(values, headerIndex, "tendon_force_kn"));
        Add(features, GetFloat(values, headerIndex, "tendon_area_mm2"));

        Add(features, spanLengths.Count > 0 ? spanLengths.Average() : 0f);
        Add(features, spanLengths.Count > 0 ? spanLengths.Min() : 0f);
        Add(features, spanLengths.Count > 0 ? spanLengths.Max() : 0f);

        for (int i = 0; i < MaxSpans; i++)
        {
            Add(features, GetListValue(spanLengths, i));
            Add(features, i < spanLengths.Count ? 1f : 0f);
            Add(features, GetListValue(beamDivisions, i));
        }

        for (int i = 0; i < MaxSpans; i++)
        {
            int spanNumber = i + 1;

            var spanLength = GetListValue(spanLengths, i);
            var udlFromList = GetListValue(udlValues, i);

            var udl = GetFloat(
                values,
                headerIndex,
                $"span_{spanNumber}_udl_kn_per_m",
                udlFromList);

            Add(features, udl);

            Add(features, GetFloat(
                values,
                headerIndex,
                $"span_{spanNumber}_udl_mask",
                i < udlValues.Count ? 1f : 0f));

            Add(features, GetFloat(
                values,
                headerIndex,
                $"span_{spanNumber}_udl_loaded",
                Math.Abs(udl) > 1e-6f ? 1f : 0f));

            Add(features, GetFloat(
                values,
                headerIndex,
                $"span_{spanNumber}_udl_total_load_kn",
                udl * spanLength));

            Add(features, GetFloat(
                values,
                headerIndex,
                $"span_{spanNumber}_length_m_for_udl",
                spanLength));
        }

        Add(features, GetFloat(values, headerIndex, "udl_total_load_kn"));
        Add(features, GetFloat(values, headerIndex, "udl_loaded_span_count"));
        Add(features, GetFloat(values, headerIndex, "udl_mean_kn_per_m"));
        Add(features, GetFloat(values, headerIndex, "udl_max_kn_per_m"));
        Add(features, GetFloat(values, headerIndex, "udl_min_kn_per_m"));

        for (int i = 0; i < MaxTendonControlPoints; i++)
        {
            Add(features, GetListValue(tendonEcc, i));
        }

        for (int i = 0; i < MaxTendonControlPoints; i++)
        {
            Add(features, i < tendonEcc.Count ? 1f : 0f);
        }


        if (features.Count != FeatureCount)
        {
            throw new InvalidOperationException(
                $"Internal feature builder error. Expected {FeatureCount} features, got {features.Count}.");
        }

        return features.ToArray();
    }

    private static List<string> BuildFeatureNames()
    {
        var names = new List<string>();

        names.Add("n_spans");
        names.Add("total_span_length_m");
        names.Add("total_divisions");
        names.Add("tendon_control_points_per_span");
        names.Add("beam_height_m");
        names.Add("beam_width_m");
        names.Add("tendon_cover_m");
        names.Add("n_tendons");
        names.Add("tendon_force_kn");
        names.Add("tendon_area_mm2");

        names.Add("span_length_mean_m");
        names.Add("span_length_min_m");
        names.Add("span_length_max_m");

        for (int i = 1; i <= MaxSpans; i++)
        {
            names.Add($"span_{i}_length_m");
            names.Add($"span_{i}_exists_mask");
            names.Add($"span_{i}_beam_divisions");
        }

        for (int i = 1; i <= MaxSpans; i++)
        {
            names.Add($"span_{i}_udl_kn_per_m");
            names.Add($"span_{i}_udl_mask");
            names.Add($"span_{i}_udl_loaded");
            names.Add($"span_{i}_udl_total_load_kn");
            names.Add($"span_{i}_length_m_for_udl");
        }

        names.Add("udl_total_load_kn");
        names.Add("udl_loaded_span_count");
        names.Add("udl_mean_kn_per_m");
        names.Add("udl_max_kn_per_m");
        names.Add("udl_min_kn_per_m");

        for (int i = 0; i < MaxTendonControlPoints; i++)
            names.Add($"tendon_ecc_cp_{i}");

        for (int i = 0; i < MaxTendonControlPoints; i++)
            names.Add($"tendon_ecc_cp_{i}_mask");


        return names;
    }

    private static void Add(List<float> features, float value)
    {
        if (float.IsNaN(value) || float.IsInfinity(value))
            features.Add(0f);
        else
            features.Add(value);
    }


    private static float GetListValue(IReadOnlyList<float> values, int index)
    {
        if (index < 0 || index >= values.Count)
            return 0f;

        return values[index];
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

    private static float GetFloat(
        string[] values,
        IReadOnlyDictionary<string, int> headerIndex,
        string columnName,
        float defaultValue = 0f)
    {
        var raw = GetString(values, headerIndex, columnName);

        if (string.IsNullOrWhiteSpace(raw))
            return defaultValue;

        if (!float.TryParse(raw, NumberStyles.Float, CultureInfo.InvariantCulture, out var result))
            return defaultValue;

        if (float.IsNaN(result) || float.IsInfinity(result))
            return defaultValue;

        return result;
    }

    private static List<float> ParseFloatList(string value)
    {
        if (string.IsNullOrWhiteSpace(value))
            return [];

        return value
            .Split(';', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries)
            .Select(x =>
            {
                if (float.TryParse(x, NumberStyles.Float, CultureInfo.InvariantCulture, out var parsed))
                    return parsed;

                return 0f;
            })
            .ToList();
    }
}
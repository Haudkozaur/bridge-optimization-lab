namespace BridgeEAApp.Surrogate;

public static class MultiSpanFeatureBuilder
{
    public const int MaxSpans = BridgeCandidate.MaxSpans;
    public const int MaxTendonControlPoints = BridgeCandidate.MaxTendonControlPoints;
    public const int FeatureCount = 180;

    public static IReadOnlyList<string> FeatureNames { get; } =
        BuildFeatureNames();

    public static float[] Build(BridgeCandidate candidate)
    {
        candidate.Validate();

        var features = new List<float>(FeatureCount);

        var activeSpanLengths = candidate.SpanLengthsM
            .Take(candidate.NSpans)
            .ToArray();

        var activeUdls = candidate.UdlValuesKnPerM
            .Take(candidate.NSpans)
            .ToArray();

        features.Add(candidate.NSpans);
        features.Add(candidate.TotalSpanLengthM);
        features.Add(candidate.TotalDivisions);
        features.Add(BridgeCandidate.TendonControlPointsPerSpan);
        features.Add(candidate.BeamHeightM);
        features.Add(candidate.BeamWidthM);
        features.Add(candidate.TendonCoverM);
        features.Add(candidate.NTendons);
        features.Add(candidate.TendonForceKn);
        features.Add(candidate.TendonAreaMm2);

        features.Add(activeSpanLengths.Average());
        features.Add(activeSpanLengths.Min());
        features.Add(activeSpanLengths.Max());

        for (var i = 0; i < MaxSpans; i++)
        {
            var spanExists = i < candidate.NSpans;

            features.Add(spanExists ? candidate.SpanLengthsM[i] : 0.0f);
            features.Add(spanExists ? 1.0f : 0.0f);
            features.Add(spanExists ? candidate.BeamDivisions[i] : 0.0f);
        }

        for (var i = 0; i < MaxSpans; i++)
        {
            var spanExists = i < candidate.NSpans;

            var spanLength = spanExists
                ? candidate.SpanLengthsM[i]
                : 0.0f;

            var udl = spanExists
                ? candidate.UdlValuesKnPerM[i]
                : 0.0f;

            var udlMask = spanExists ? 1.0f : 0.0f;

            var udlLoaded =
                spanExists && Math.Abs(udl) > 1.0e-6f
                    ? 1.0f
                    : 0.0f;

            var udlTotalLoad = udl * spanLength;

            features.Add(udl);
            features.Add(udlMask);
            features.Add(udlLoaded);
            features.Add(udlTotalLoad);
            features.Add(spanLength);
        }

        var totalUdlLoad = 0.0f;
        var loadedSpanCount = 0;

        for (var i = 0; i < candidate.NSpans; i++)
        {
            var udl = candidate.UdlValuesKnPerM[i];
            var spanLength = candidate.SpanLengthsM[i];

            totalUdlLoad += udl * spanLength;

            if (Math.Abs(udl) > 1.0e-6f)
                loadedSpanCount++;
        }

        features.Add(totalUdlLoad);
        features.Add(loadedSpanCount);
        features.Add(activeUdls.Average());
        features.Add(activeUdls.Max());
        features.Add(activeUdls.Min());

        for (var i = 0; i < MaxTendonControlPoints; i++)
            features.Add(candidate.TendonEccControlPointsM[i]);

        var activeTendonCpCount = candidate.ActiveTendonControlPointCount;

        for (var i = 0; i < MaxTendonControlPoints; i++)
            features.Add(i < activeTendonCpCount ? 1.0f : 0.0f);

        if (features.Count != FeatureCount)
        {
            throw new Exception(
                $"Feature vector size mismatch. Expected {FeatureCount}, got {features.Count}.");
        }

        if (FeatureNames.Count != FeatureCount)
        {
            throw new Exception(
                $"Feature names size mismatch. Expected {FeatureCount}, got {FeatureNames.Count}.");
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
}
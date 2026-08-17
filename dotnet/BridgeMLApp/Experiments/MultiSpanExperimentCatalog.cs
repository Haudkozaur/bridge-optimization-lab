using BridgeMLApp.Domain;

namespace BridgeMLApp.Experiments;

public static class MultiSpanExperimentCatalog
{
    public const int MaxSpans = 10;
    public const int MaxSupports = MaxSpans + 1;

    private static readonly string[] LoadCases =
    [
        "dl",
        "ps",
        "total"
    ];

    public static IEnumerable<MlExperiment> SmokeTests()
    {
        yield return TotalSpanMomentAbsMax(1);
        yield return TotalSpanDeflectionAbsMax(1);
        yield return TotalSupportMomentAbsMax(1);
        yield return TotalSupportReactionFz(1);
    }

    // Najważniejszy zestaw na teraz:
    // wszystkie przęsła + wszystkie podpory, tylko loadcase TOTAL.
    public static IEnumerable<MlExperiment> AllTotalExperiments()
    {
        return AllForLoadCase("total");
    }

    // Jak potem będziemy chcieli też DL i PS.
    public static IEnumerable<MlExperiment> AllLoadCaseExperiments()
    {
        foreach (var loadCase in LoadCases)
        {
            foreach (var experiment in AllForLoadCase(loadCase))
                yield return experiment;
        }
    }

    public static IEnumerable<MlExperiment> AllForLoadCase(string loadCase)
    {
        loadCase = NormalizeLoadCase(loadCase);

        for (int span = 1; span <= MaxSpans; span++)
        {
            yield return SpanDeflectionAbsMax(loadCase, span);

            yield return SpanMomentMin(loadCase, span);
            yield return SpanMomentMax(loadCase, span);
            yield return SpanMomentAbsMax(loadCase, span);
        }

        for (int support = 0; support < MaxSupports; support++)
        {
            yield return SupportDeflectionAbsMax(loadCase, support);

            yield return SupportMomentMin(loadCase, support);
            yield return SupportMomentMax(loadCase, support);
            yield return SupportMomentAbsMax(loadCase, support);

            yield return SupportReactionFz(loadCase, support);
        }
    }

    public static MlExperiment TotalSpanMomentAbsMax(int spanIndex)
    {
        return SpanMomentAbsMax("total", spanIndex);
    }

    public static MlExperiment TotalSpanDeflectionAbsMax(int spanIndex)
    {
        return SpanDeflectionAbsMax("total", spanIndex);
    }

    public static MlExperiment TotalSupportMomentAbsMax(int supportIndex)
    {
        return SupportMomentAbsMax("total", supportIndex);
    }

    public static MlExperiment TotalSupportReactionFz(int supportIndex)
    {
        return SupportReactionFz("total", supportIndex);
    }

    public static MlExperiment SpanDeflectionAbsMax(string loadCase, int spanIndex)
    {
        ValidateSpanIndex(spanIndex);
        loadCase = NormalizeLoadCase(loadCase);

        return Create(
            name: $"{loadCase}_deflection_span_{spanIndex}_middle_zone_abs_max",
            targetColumn: $"deflections_dz_{loadCase}_span_{spanIndex}_middle_zone_abs_max");
    }

    public static MlExperiment SupportDeflectionAbsMax(string loadCase, int supportIndex)
    {
        ValidateSupportIndex(supportIndex);
        loadCase = NormalizeLoadCase(loadCase);

        return Create(
            name: $"{loadCase}_deflection_support_{supportIndex}_zone_abs_max",
            targetColumn: $"deflections_dz_{loadCase}_support_{supportIndex}_zone_abs_max");
    }

    public static MlExperiment SpanMomentMin(string loadCase, int spanIndex)
    {
        ValidateSpanIndex(spanIndex);
        loadCase = NormalizeLoadCase(loadCase);

        return Create(
            name: $"{loadCase}_moment_span_{spanIndex}_middle_zone_min",
            targetColumn: $"moments_my_{loadCase}_span_{spanIndex}_middle_zone_min");
    }

    public static MlExperiment SpanMomentMax(string loadCase, int spanIndex)
    {
        ValidateSpanIndex(spanIndex);
        loadCase = NormalizeLoadCase(loadCase);

        return Create(
            name: $"{loadCase}_moment_span_{spanIndex}_middle_zone_max",
            targetColumn: $"moments_my_{loadCase}_span_{spanIndex}_middle_zone_max");
    }

    public static MlExperiment SpanMomentAbsMax(string loadCase, int spanIndex)
    {
        ValidateSpanIndex(spanIndex);
        loadCase = NormalizeLoadCase(loadCase);

        return Create(
            name: $"{loadCase}_moment_span_{spanIndex}_middle_zone_abs_max",
            targetColumn: $"moments_my_{loadCase}_span_{spanIndex}_middle_zone_abs_max");
    }

    public static MlExperiment SupportMomentMin(string loadCase, int supportIndex)
    {
        ValidateSupportIndex(supportIndex);
        loadCase = NormalizeLoadCase(loadCase);

        return Create(
            name: $"{loadCase}_moment_support_{supportIndex}_zone_min",
            targetColumn: $"moments_my_{loadCase}_support_{supportIndex}_zone_min");
    }

    public static MlExperiment SupportMomentMax(string loadCase, int supportIndex)
    {
        ValidateSupportIndex(supportIndex);
        loadCase = NormalizeLoadCase(loadCase);

        return Create(
            name: $"{loadCase}_moment_support_{supportIndex}_zone_max",
            targetColumn: $"moments_my_{loadCase}_support_{supportIndex}_zone_max");
    }

    public static MlExperiment SupportMomentAbsMax(string loadCase, int supportIndex)
    {
        ValidateSupportIndex(supportIndex);
        loadCase = NormalizeLoadCase(loadCase);

        return Create(
            name: $"{loadCase}_moment_support_{supportIndex}_zone_abs_max",
            targetColumn: $"moments_my_{loadCase}_support_{supportIndex}_zone_abs_max");
    }

    public static MlExperiment SupportReactionFz(string loadCase, int supportIndex)
    {
        ValidateSupportIndex(supportIndex);
        loadCase = NormalizeLoadCase(loadCase);

        return Create(
            name: $"{loadCase}_reaction_fz_support_{supportIndex}",
            targetColumn: $"reactions_fz_{loadCase}_support_{supportIndex}");
    }

    private static MlExperiment Create(string name, string targetColumn)
    {
        return new MlExperiment
        {
            Name = name,
            TargetColumn = targetColumn,
            FeatureColumns = []
        };
    }

    private static string NormalizeLoadCase(string loadCase)
    {
        loadCase = loadCase.Trim().ToLowerInvariant();

        if (!LoadCases.Contains(loadCase))
            throw new ArgumentException($"Unsupported load case: {loadCase}");

        return loadCase;
    }

    private static void ValidateSpanIndex(int spanIndex)
    {
        if (spanIndex < 1 || spanIndex > MaxSpans)
            throw new ArgumentOutOfRangeException(
                nameof(spanIndex),
                $"Span index must be from 1 to {MaxSpans}.");
    }

    private static void ValidateSupportIndex(int supportIndex)
    {
        if (supportIndex < 0 || supportIndex >= MaxSupports)
            throw new ArgumentOutOfRangeException(
                nameof(supportIndex),
                $"Support index must be from 0 to {MaxSupports - 1}.");
    }
}
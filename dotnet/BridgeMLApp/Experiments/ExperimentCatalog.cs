using BridgeMLApp.Domain;

namespace BridgeMLApp.Experiments;

public static class ExperimentCatalog
{
    public static MlExperiment MiddleHyperstaticReaction => new()
    {
        Name = "ps_middle_hyperstatic_reaction",
        TargetColumn = "reactions_fz_ps_middle",
        FeatureColumns =
        [
            "left_span_length_m",
            "right_span_length_m",
            "tendon_ecc_left_m",
            "tendon_ecc_left_span_mid_m",
            "tendon_ecc_mid_support_m",
            "tendon_ecc_right_span_mid_m",
            "tendon_ecc_right_m"
        ]
    };


    public static MlExperiment TotalMomentLeftSpanAbsMax => new()
    {
        Name = "total_moment_left_span_abs_max",
        TargetColumn = "moments_my_total_left_span_abs_max",
        FeatureColumns = BasicTendonGeometryFeatures
    };

    public static MlExperiment TotalMomentMiddleSupport => new()
    {
        Name = "total_moment_middle_support",
        TargetColumn = "moments_my_total_middle_support",
        FeatureColumns = BasicTendonGeometryFeatures
    };

    public static MlExperiment TotalMomentRightSpanAbsMax => new()
    {
        Name = "total_moment_right_span_abs_max",
        TargetColumn = "moments_my_total_right_span_abs_max",
        FeatureColumns = BasicTendonGeometryFeatures
    };
    public static MlExperiment TotalMomentLeftSpanMin => new()
    {
        Name = "total_moment_left_span_min",
        TargetColumn = "moments_my_total_left_span_min",
        FeatureColumns = BasicTendonGeometryFeatures
    };

    public static MlExperiment TotalMomentLeftSpanMax => new()
    {
        Name = "total_moment_left_span_max",
        TargetColumn = "moments_my_total_left_span_max",
        FeatureColumns = BasicTendonGeometryFeatures
    };



    public static MlExperiment TotalMomentRightSpanMin => new()
    {
        Name = "total_moment_right_span_min",
        TargetColumn = "moments_my_total_right_span_min",
        FeatureColumns = BasicTendonGeometryFeatures
    };

    public static MlExperiment TotalMomentRightSpanMax => new()
    {
        Name = "total_moment_right_span_max",
        TargetColumn = "moments_my_total_right_span_max",
        FeatureColumns = BasicTendonGeometryFeatures
    };

    public static MlExperiment TotalDeflectionLeftSpanMin => new()
    {
        Name = "total_deflection_left_span_min",
        TargetColumn = "deflections_dz_total_left_span_min",
        FeatureColumns = BasicTendonGeometryFeatures
    };

    public static MlExperiment TotalDeflectionLeftSpanMax => new()
    {
        Name = "total_deflection_left_span_max",
        TargetColumn = "deflections_dz_total_left_span_max",
        FeatureColumns = BasicTendonGeometryFeatures
    };

    public static MlExperiment TotalDeflectionRightSpanMin => new()
    {
        Name = "total_deflection_right_span_min",
        TargetColumn = "deflections_dz_total_right_span_min",
        FeatureColumns = BasicTendonGeometryFeatures
    };

    public static MlExperiment TotalDeflectionRightSpanMax => new()
    {
        Name = "total_deflection_right_span_max",
        TargetColumn = "deflections_dz_total_right_span_max",
        FeatureColumns = BasicTendonGeometryFeatures
    };


    public static MlExperiment TotalDeflectionLeftSpanAbsMax => new()
    {
        Name = "total_deflection_left_span_abs_max",
        TargetColumn = "deflections_dz_total_left_span_abs_max",
        FeatureColumns = BasicTendonGeometryFeatures
    };

    public static MlExperiment TotalDeflectionRightSpanAbsMax => new()
    {
        Name = "total_deflection_right_span_abs_max",
        TargetColumn = "deflections_dz_total_right_span_abs_max",
        FeatureColumns = BasicTendonGeometryFeatures
    };

    private static string[] BasicTendonGeometryFeatures =>
    [
        "left_span_length_m",
        "right_span_length_m",
        "udl_kn_per_m",
        "tendon_ecc_left_m",
        "tendon_ecc_left_span_mid_m",
        "tendon_ecc_mid_support_m",
        "tendon_ecc_right_span_mid_m",
        "tendon_ecc_right_m"
    ];

    public static MlExperiment TotalMomentLeftSupportFromLeftEcc => new()
    {
        Name = "total_moment_left_support_from_left_ecc",
        TargetColumn = "moments_my_total_left_support",
        FeatureColumns =
    [
        "tendon_ecc_left_m"
    ]
    };

    public static MlExperiment TotalMomentRightSupportFromRightEcc => new()
    {
        Name = "total_moment_right_support_from_right_ecc",
        TargetColumn = "moments_my_total_right_support",
        FeatureColumns =
        [
            "tendon_ecc_right_m"
        ]
    };
}
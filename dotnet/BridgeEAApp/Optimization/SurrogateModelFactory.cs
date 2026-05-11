using BridgeEAApp.Optimization;

namespace BridgeEAApp.Surrogate;

internal static class SurrogateModelFactory
{
    public static BridgeFitnessEvaluator CreateDefault(string modelsDirectory)
    {
        MlSurrogateModel Load(string fileName, bool includeUdl)
        {
            return new MlSurrogateModel(
                Path.Combine(modelsDirectory, fileName),
                includeUdl);
        }

        var middlePsReactionModel = Load(
            "ps_middle_hyperstatic_reaction_LightGbm.zip",
            includeUdl: false);

        var middleTotalMomentModel = Load(
            "total_moment_middle_support_LightGbm.zip",
            includeUdl: true);

        var leftDeflectionMinModel = Load(
            "total_deflection_left_span_min_LightGbm.zip",
            includeUdl: true);

        var leftDeflectionMaxModel = Load(
            "total_deflection_left_span_max_LightGbm.zip",
            includeUdl: true);

        var rightDeflectionMinModel = Load(
            "total_deflection_right_span_min_LightGbm.zip",
            includeUdl: true);

        var rightDeflectionMaxModel = Load(
            "total_deflection_right_span_max_LightGbm.zip",
            includeUdl: true);

        var leftMomentMinModel = Load(
            "total_moment_left_span_min_LightGbm.zip",
            includeUdl: true);

        var leftMomentMaxModel = Load(
            "total_moment_left_span_max_LightGbm.zip",
            includeUdl: true);

        var rightMomentMinModel = Load(
            "total_moment_right_span_min_LightGbm.zip",
            includeUdl: true);

        var rightMomentMaxModel = Load(
            "total_moment_right_span_max_LightGbm.zip",
            includeUdl: true);

        return new BridgeFitnessEvaluator(
            middlePsReactionModel,
            middleTotalMomentModel,
            leftDeflectionMinModel,
            leftDeflectionMaxModel,
            rightDeflectionMinModel,
            rightDeflectionMaxModel,
            leftMomentMinModel,
            leftMomentMaxModel,
            rightMomentMinModel,
            rightMomentMaxModel);
    }
}
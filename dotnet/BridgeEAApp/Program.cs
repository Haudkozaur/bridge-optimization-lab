using BridgeEAApp.Optimization;
using BridgeEAApp.Reporting;
using BridgeEAApp.Surrogate;

var root = Path.GetFullPath(
    Path.Combine(
        AppDomain.CurrentDomain.BaseDirectory,
        @"..\..\..\..\"));

var modelsDir = Path.Combine(root, "models");

var fitnessEvaluator =
    SurrogateModelFactory.CreateDefault(modelsDir);

var optimizer = new RandomSearchOptimizer();

var optimizationMode =
    OptimizationMode.MutationWithRandomRestart;
    //OptimizationMode.MutationAroundBest;
    //OptimizationMode.MonteCarlo;

var best = optimizer.Optimize(
    leftSpanLengthM: 20.0f,
    rightSpanLengthM: 20.0f,
    udlKnPerM: 10f,
    iterations: 1_000_000,
    patience: 100_000,
    mode: optimizationMode,
    fitnessEvaluator);

var bestResult =
    fitnessEvaluator.EvaluateDetailed(best);

ConsoleResultPrinter.PrintBestCandidate(
    best,
    bestResult);
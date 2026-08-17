using BridgeEAApp.Optimization;
using BridgeEAApp.Surrogate;

namespace BridgeEAApp.Reporting;

internal static class ConsoleResultPrinter
{
    public static void PrintBestCandidate(
        BridgeCandidate best,
        BridgeFitnessResult result)
    {
        Console.WriteLine();
        Console.WriteLine("=== BEST CANDIDATE ===");
        Console.WriteLine($"Fitness:                 {result.Fitness:F6}");
        Console.WriteLine($"Structural score:        {result.StructuralScore:F6}");
        Console.WriteLine($"Deflection score:        {result.DeflectionScore:F6}");
        Console.WriteLine($"Span moment score:       {result.SpanMomentScore:F6}");
        Console.WriteLine($"Support moment score:    {result.SupportMomentScore:F6}");
        Console.WriteLine($"Reaction score:          {result.ReactionScore:F6}");
        // Console.WriteLine($"Cover penalty:           {result.CoverPenaltyScore:F6}");
        // Console.WriteLine($"Smoothness penalty:      {result.SmoothnessPenaltyScore:F6}");
        // Console.WriteLine($"Jump penalty:            {result.JumpPenaltyScore:F6}");
        Console.WriteLine($"Symmetry penalty:        {result.SymmetryPenaltyApplied}");
        Console.WriteLine($"Symmetry score:          {result.SymmetryScore:F6}");

        Console.WriteLine();
        Console.WriteLine("=== GEOMETRY ===");
        Console.WriteLine($"N spans:                 {best.NSpans}");
        Console.WriteLine($"Total length:            {best.TotalSpanLengthM:F3} m");
        Console.WriteLine($"Total divisions:         {best.TotalDivisions}");
        Console.WriteLine($"Beam height:             {best.BeamHeightM:F3} m");
        Console.WriteLine($"Beam width:              {best.BeamWidthM:F3} m");
        Console.WriteLine($"Tendon cover:            {best.TendonCoverM:F3} m");
        Console.WriteLine($"N tendons:               {best.NTendons}");
        Console.WriteLine($"Tendon force:            {best.TendonForceKn:F3} kN");
        Console.WriteLine($"Tendon area:             {best.TendonAreaMm2:F3} mm2");

        Console.WriteLine();
        Console.WriteLine("=== SPANS ===");

        for (var i = 0; i < best.NSpans; i++)
        {
            Console.WriteLine(
                $"Span {i + 1,2}: " +
                $"L = {best.SpanLengthsM[i],7:F3} m | " +
                $"UDL = {best.UdlValuesKnPerM[i],7:F3} kN/m | " +
                $"dz_abs = {result.SpanDeflectionAbsMax[i],10:F6} | " +
                $"Mmin = {result.SpanMomentMin[i],10:F3} | " +
                $"Mmax = {result.SpanMomentMax[i],10:F3} | " +
                $"Mabs = {result.SpanMomentAbsMax[i],10:F3}");
        }

        Console.WriteLine();
        Console.WriteLine("=== SUPPORTS ===");

        for (var i = 0; i <= best.NSpans; i++)
        {
            Console.WriteLine(
                $"Support {i,2}: " +
                $"dz_abs = {result.SupportDeflectionAbsMax[i],10:F6} | " +
                $"Mmin = {result.SupportMomentMin[i],10:F3} | " +
                $"Mmax = {result.SupportMomentMax[i],10:F3} | " +
                $"Mabs = {result.SupportMomentAbsMax[i],10:F3} | " +
                $"Fz = {result.SupportReactionFz[i],10:F3}");
        }

        Console.WriteLine();
        Console.WriteLine("=== TENDON ECCENTRICITIES ===");
        Console.WriteLine(
            string.Join(
                ";",
                best.TendonEccControlPointsM
                    .Take(best.ActiveTendonControlPointCount)
                    .Select(x => x.ToString("F3"))));
    }
}
namespace BridgeEAApp.Surrogate;

public class BridgeCandidate
{
    public const int MaxSpans = 10;
    public const int MaxSupports = MaxSpans + 1;

    public const int TendonControlPointsPerSpan = 5;
    public const int MaxTendonControlPoints = 4 * MaxSpans + 1;

    public int NSpans { get; set; }

    public float[] SpanLengthsM { get; set; } =
        new float[MaxSpans];

    public int[] BeamDivisions { get; set; } =
        new int[MaxSpans];

    public float[] UdlValuesKnPerM { get; set; } =
        new float[MaxSpans];

    public float BeamHeightM { get; set; } = 1.0f;
    public float BeamWidthM { get; set; } = 0.5f;
    public float TendonCoverM { get; set; } = 0.05f;

    public int NTendons { get; set; } = 3;
    public float TendonForceKn { get; set; } = 220.0f;
    public float TendonAreaMm2 { get; set; } = 150.0f;

    public float[] TendonEccControlPointsM { get; set; } =
        new float[MaxTendonControlPoints];

    public int ActiveTendonControlPointCount =>
        4 * NSpans + 1;

    public float TotalSpanLengthM =>
        SpanLengthsM.Take(NSpans).Sum();

    public int TotalDivisions =>
        BeamDivisions.Take(NSpans).Sum();

    public void Validate()
    {
        if (NSpans < 2 || NSpans > MaxSpans)
            throw new Exception($"NSpans must be between 2 and {MaxSpans}.");

        if (SpanLengthsM.Length != MaxSpans)
            throw new Exception($"SpanLengthsM must have length {MaxSpans}.");

        if (BeamDivisions.Length != MaxSpans)
            throw new Exception($"BeamDivisions must have length {MaxSpans}.");

        if (UdlValuesKnPerM.Length != MaxSpans)
            throw new Exception($"UdlValuesKnPerM must have length {MaxSpans}.");

        if (TendonEccControlPointsM.Length != MaxTendonControlPoints)
            throw new Exception(
                $"TendonEccControlPointsM must have length {MaxTendonControlPoints}.");

        for (var i = 0; i < NSpans; i++)
        {
            if (SpanLengthsM[i] <= 0.0f)
                throw new Exception($"Span {i + 1} length must be > 0.");

            if (BeamDivisions[i] <= 0)
                throw new Exception($"Span {i + 1} divisions must be > 0.");
        }

        if (BeamHeightM <= 0.0f)
            throw new Exception("BeamHeightM must be > 0.");

        if (BeamWidthM <= 0.0f)
            throw new Exception("BeamWidthM must be > 0.");

        if (TendonCoverM < 0.0f)
            throw new Exception("TendonCoverM must be >= 0.");

        if (NTendons <= 0)
            throw new Exception("NTendons must be > 0.");

        if (TendonForceKn <= 0.0f)
            throw new Exception("TendonForceKn must be > 0.");

        if (TendonAreaMm2 <= 0.0f)
            throw new Exception("TendonAreaMm2 must be > 0.");

        for (var i = 0; i < ActiveTendonControlPointCount; i++)
        {
            var ecc = TendonEccControlPointsM[i];

            if (float.IsNaN(ecc) || float.IsInfinity(ecc))
                throw new Exception($"Invalid tendon eccentricity at cp {i}: {ecc}");
        }
    }

    public BridgeCandidate Clone()
    {
        return new BridgeCandidate
        {
            NSpans = NSpans,

            SpanLengthsM = (float[])SpanLengthsM.Clone(),
            BeamDivisions = (int[])BeamDivisions.Clone(),
            UdlValuesKnPerM = (float[])UdlValuesKnPerM.Clone(),

            BeamHeightM = BeamHeightM,
            BeamWidthM = BeamWidthM,
            TendonCoverM = TendonCoverM,

            NTendons = NTendons,
            TendonForceKn = TendonForceKn,
            TendonAreaMm2 = TendonAreaMm2,

            TendonEccControlPointsM =
                (float[])TendonEccControlPointsM.Clone()
        };
    }
}
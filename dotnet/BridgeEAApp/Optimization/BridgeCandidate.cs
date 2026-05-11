namespace BridgeEAApp.Surrogate;

public class BridgeCandidate
{
    public float LeftSpanLengthM { get; set; }
    public float RightSpanLengthM { get; set; }
    public float UdlKnPerM { get; set; }

    public float TendonEccLeftM { get; set; }
    public float TendonEccLeftSpanMidM { get; set; }
    public float TendonEccMidSupportM { get; set; }
    public float TendonEccRightSpanMidM { get; set; }
    public float TendonEccRightM { get; set; }

    public float[] ToFeatures(bool includeUdl)
    {
        if (includeUdl)
        {
            return
            [
                LeftSpanLengthM,
                RightSpanLengthM,
                UdlKnPerM,
                TendonEccLeftM,
                TendonEccLeftSpanMidM,
                TendonEccMidSupportM,
                TendonEccRightSpanMidM,
                TendonEccRightM
            ];
        }

        return
        [
            LeftSpanLengthM,
            RightSpanLengthM,
            TendonEccLeftM,
            TendonEccLeftSpanMidM,
            TendonEccMidSupportM,
            TendonEccRightSpanMidM,
            TendonEccRightM
        ];
    }
}
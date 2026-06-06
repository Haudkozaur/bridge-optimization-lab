from enum import Enum

class Model_Type(Enum):
    SINGLE_SPAN_BEAM = "single_span_beam"
    SINGLE_SPAN_POST_TENSIONED_BEAM = "single_span_post_tensioned_beam"
    TWO_SPAN_POST_TENSIONED_BEAM = "two_span_post_tensioned_beam"
    FIXED_PARAMS_TWO_SPAN_POST_TENSIONED_BEAM = "fixed_params_two_span_post_tensioned_beam"
    SINGLE_SPAN_BRIDGE = "single_span_bridge"
    MULTI_SPAN_BEAM = "multi_span_beam"
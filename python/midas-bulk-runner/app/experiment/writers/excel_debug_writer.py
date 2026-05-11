from pathlib import Path
import polars as pl
from midas_civil import Result


class ExcelDebugWriter:
    def __init__(self, output_dir: str | Path, file_name: str = "results_debug.xlsx"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.excel_path = self.output_dir / file_name

    def dump_debug_tables(self, model_meta: dict) -> None:
        loadcases = [
            model_meta["self_weight_result_name"],
            model_meta["udl_case_result_name"],
        ]

        if "prestress_case_result_name" in model_meta:
            loadcases.append(model_meta["prestress_case_result_name"])

        beam_ids = model_meta["beam_ids"]
        mid_index = len(beam_ids) // 2

        if len(beam_ids) % 2 == 0:
            mid_beam_ids = [beam_ids[mid_index - 1], beam_ids[mid_index]]
        else:
            mid_beam_ids = [beam_ids[mid_index]]

        self._dump_result_table_to_excel(
            table_type="DISPLACEMENTG",
            keys=model_meta["mid_nodes"],
            loadcases=loadcases,
            sheet_name="mid_disp",
        )

        self._dump_result_table_to_excel(
            table_type="REACTIONG",
            keys=model_meta["left_nodes"],
            loadcases=loadcases,
            sheet_name="left_reaction",
        )

        self._dump_result_table_to_excel(
            table_type="REACTIONG",
            keys=model_meta["right_nodes"],
            loadcases=loadcases,
            sheet_name="right_reaction",
        )

        self._dump_beam_force_to_excel(
            beam_ids=mid_beam_ids,
            loadcases=loadcases,
            sheet_name="mid_beam_force",
            parts=["PartI", "Part1/4", "PartJ"],
            components=["all"],
        )

        if "prestress_case_result_name" in model_meta:
            self._dump_beam_force_prestress_to_excel(
                beam_ids=mid_beam_ids,
                loadcases=[model_meta["prestress_case_result_name"]],
                sheet_name="mid_beam_prestress",
                parts=["PartI", "Part1/4", "PartJ"],
                components=["all"],
            )

    def _dump_result_table_to_excel(
        self,
        table_type: str,
        keys: list[int],
        loadcases: list[str],
        sheet_name: str,
    ) -> None:
        df = Result.TABLE(
            table_type,
            keys=keys,
            loadcase=loadcases,
        )
        self._write_df_to_excel(df, sheet_name)

    def _dump_beam_force_to_excel(
        self,
        beam_ids: list[int],
        loadcases: list[str],
        sheet_name: str,
        parts: list[str] | None = None,
        components: list[str] | None = None,
    ) -> None:
        if parts is None:
            parts = ["PartI", "PartJ"]

        if components is None:
            components = ["all"]

        df = Result.TABLE.BeamForce(
            keys=beam_ids,
            loadcase=loadcases,
            parts=parts,
            components=components,
        )
        self._write_df_to_excel(df, sheet_name)

    def _dump_beam_force_prestress_to_excel(
        self,
        beam_ids: list[int],
        loadcases: list[str],
        sheet_name: str,
        parts: list[str] | None = None,
        components: list[str] | None = None,
    ) -> None:
        if parts is None:
            parts = ["PartI", "PartJ"]

        if components is None:
            components = ["all"]

        df = Result.TABLE.BeamForce_StaticPrestress(
            keys=beam_ids,
            loadcase=loadcases,
            parts=parts,
            components=components,
        )
        self._write_df_to_excel(df, sheet_name)

    def _dump_user_defined_table_to_excel(
        self,
        table_name: str,
        sheet_name: str,
        summary: int = 0,
    ) -> None:
        df = Result.UserDefinedTable(
            table_name,
            summary=summary,
            force_unit="KN",
            len_unit="M",
        )
        self._write_df_to_excel(df, sheet_name)

    def _write_df_to_excel(self, df, sheet_name: str) -> None:
        if df is None:
            return

        if getattr(df, "height", 0) == 0:
            return

        if not isinstance(df, pl.DataFrame):
            return

        if not self.excel_path.exists():
            self.excel_path.touch()

        df.write_excel(
            workbook=str(self.excel_path),
            worksheet=sheet_name,
        )
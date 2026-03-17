"""Unit tests for text2sample task-type support in LLM input preparation."""

from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from acestep.api.job_llm_preparation import prepare_llm_generation_inputs


class Text2SampleInputPreparationTests(unittest.TestCase):
    """Verify that task_type='text2sample' auto-enables sample_mode behavior."""

    def _base_req(self) -> SimpleNamespace:
        return SimpleNamespace(
            lm_model_path="",
            lm_backend="",
            lm_temperature=0.85,
            lm_top_k=0,
            lm_top_p=0.9,
            thinking=False,
            sample_mode=False,
            sample_query="",
            use_format=False,
            use_cot_caption=False,
            use_cot_language=False,
            full_analysis_only=False,
            prompt="",
            lyrics="",
            bpm=None,
            key_scale="",
            time_signature="",
            audio_duration=None,
            task_type="text2music",
            vocal_language="en",
        )

    def _make_sample_result(self) -> SimpleNamespace:
        return SimpleNamespace(
            success=True,
            caption="punchy drum loop",
            lyrics="[Instrumental]",
            bpm=140,
            keyscale="",
            timesignature="4/4",
            duration=8.0,
        )

    def _make_app_state(self) -> SimpleNamespace:
        return SimpleNamespace(
            _llm_initialized=True,
            _llm_init_error=None,
            _llm_lazy_load_disabled=False,
        )

    # ------------------------------------------------------------------
    # Success path
    # ------------------------------------------------------------------

    def test_text2sample_auto_enables_sample_mode(self) -> None:
        """task_type='text2sample' should implicitly trigger sample_mode."""
        req = self._base_req()
        req.task_type = "text2sample"
        req.sample_mode = False  # not explicitly set
        req.sample_query = "punchy trap drum loop at 140 BPM"

        sample_result = self._make_sample_result()
        create_fn = MagicMock(return_value=sample_result)

        prepared = prepare_llm_generation_inputs(
            app_state=self._make_app_state(),
            llm_handler=MagicMock(),
            req=req,
            selected_handler_device="cuda",
            parse_description_hints=MagicMock(return_value=(None, True)),
            create_sample_fn=create_fn,
            format_sample_fn=MagicMock(),
            ensure_llm_ready_fn=MagicMock(),
            log_fn=MagicMock(),
        )

        create_fn.assert_called_once()
        self.assertEqual(prepared.caption, "punchy drum loop")
        self.assertTrue(prepared.sample_mode)

    def test_text2sample_promotes_prompt_as_query_when_sample_query_empty(self) -> None:
        """When task_type='text2sample' and sample_query is empty, prompt is used."""
        req = self._base_req()
        req.task_type = "text2sample"
        req.sample_query = ""
        req.prompt = "funky bass loop in E minor"

        sample_result = self._make_sample_result()
        create_fn = MagicMock(return_value=sample_result)

        prepare_llm_generation_inputs(
            app_state=self._make_app_state(),
            llm_handler=MagicMock(),
            req=req,
            selected_handler_device="cuda",
            parse_description_hints=MagicMock(return_value=(None, False)),
            create_sample_fn=create_fn,
            format_sample_fn=MagicMock(),
            ensure_llm_ready_fn=MagicMock(),
            log_fn=MagicMock(),
        )

        # The create_sample_fn must be called with the promoted prompt.
        call_kwargs = create_fn.call_args
        query_used = (
            call_kwargs.kwargs.get("query") or
            (call_kwargs.args[1] if len(call_kwargs.args) > 1 else None)
        )
        self.assertEqual(query_used, "funky bass loop in E minor")

    # ------------------------------------------------------------------
    # Regression / non-target behavior
    # ------------------------------------------------------------------

    def test_text2music_does_not_auto_enable_sample_mode(self) -> None:
        """task_type='text2music' without sample_mode should NOT trigger sample_mode."""
        req = self._base_req()
        req.task_type = "text2music"
        req.sample_mode = False
        req.prompt = "calm acoustic guitar"

        create_fn = MagicMock()

        prepared = prepare_llm_generation_inputs(
            app_state=self._make_app_state(),
            llm_handler=MagicMock(),
            req=req,
            selected_handler_device="cuda",
            parse_description_hints=MagicMock(return_value=(None, False)),
            create_sample_fn=create_fn,
            format_sample_fn=MagicMock(),
            ensure_llm_ready_fn=MagicMock(),
            log_fn=MagicMock(),
        )

        create_fn.assert_not_called()
        self.assertFalse(prepared.sample_mode)
        self.assertEqual(prepared.caption, "calm acoustic guitar")


class Text2SampleConstantsTests(unittest.TestCase):
    """Verify that text2sample is registered in global constants."""

    def test_text2sample_in_task_instructions(self) -> None:
        """TASK_INSTRUCTIONS must include a text2sample entry."""
        from acestep.constants import TASK_INSTRUCTIONS
        self.assertIn("text2sample", TASK_INSTRUCTIONS)
        self.assertIsInstance(TASK_INSTRUCTIONS["text2sample"], str)
        self.assertTrue(TASK_INSTRUCTIONS["text2sample"].strip())

    def test_text2sample_in_mode_to_task_type(self) -> None:
        """MODE_TO_TASK_TYPE must map 'Sample' to 'text2sample'."""
        from acestep.constants import MODE_TO_TASK_TYPE
        self.assertIn("Sample", MODE_TO_TASK_TYPE)
        self.assertEqual(MODE_TO_TASK_TYPE["Sample"], "text2sample")

    def test_sample_mode_in_generation_modes_turbo(self) -> None:
        """GENERATION_MODES_TURBO must include 'Sample'."""
        from acestep.constants import GENERATION_MODES_TURBO
        self.assertIn("Sample", GENERATION_MODES_TURBO)

    def test_sample_mode_in_generation_modes_base(self) -> None:
        """GENERATION_MODES_BASE must include 'Sample'."""
        from acestep.constants import GENERATION_MODES_BASE
        self.assertIn("Sample", GENERATION_MODES_BASE)


if __name__ == "__main__":
    unittest.main()

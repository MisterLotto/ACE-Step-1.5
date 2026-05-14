"""Library tab: browse, preview, rate, and delete generated songs."""

from typing import Any

import gradio as gr

from acestep.ui.gradio.interfaces.library_tab_handlers import (
    delete,
    do_refresh,
    save_rating,
    select_song,
)

_SORT_CHOICES = [("Newest First", "date"), ("Name A–Z", "name"), ("Top Rated", "rating")]
_FILTER_CHOICES = [
    ("All", 0), ("★+", 1), ("★★+", 2), ("★★★+", 3), ("★★★★+", 4), ("★★★★★", 5)
]
_RATING_CHOICES = [("★", 1), ("★★", 2), ("★★★", 3), ("★★★★", 4), ("★★★★★", 5)]
_TABLE_HEADERS = ["Name", "Date", "Rating"]
_TABLE_TYPES = ["str", "str", "str"]


# ── UI builder ────────────────────────────────────────────────────────────────

def create_library_section() -> dict[str, Any]:
    """Build the Library tab UI and wire all internal events.

    Returns:
        Component map (all keys prefixed with ``lib_``).
    """
    with gr.Column():

        # ── Toolbar ──────────────────────────────────────────────────────────
        with gr.Row():
            lib_refresh_btn = gr.Button("🔄 Refresh", variant="secondary", scale=0, min_width=110)
            lib_sort = gr.Dropdown(
                choices=_SORT_CHOICES, value="date", label="Sort by", scale=1,
            )
            lib_filter = gr.Dropdown(
                choices=_FILTER_CHOICES, value=0, label="Min Rating", scale=1,
            )
            with gr.Column(scale=3):
                lib_count = gr.Markdown("")

        # ── Song table ────────────────────────────────────────────────────────
        lib_table = gr.Dataframe(
            headers=_TABLE_HEADERS,
            datatype=_TABLE_TYPES,
            value=[],
            label="Generated Songs — click any row to preview",
            interactive=False,
            wrap=True,
            column_widths=["60%", "25%", "15%"],
        )

        # State: full list of song dicts returned by scan_library()
        lib_songs_state = gr.State([])

        # ── Selected song panel ───────────────────────────────────────────────
        with gr.Group(visible=False, elem_id="lib-selected-panel") as lib_selected_panel:
            gr.Markdown("---")
            with gr.Row():
                with gr.Column(scale=3):
                    lib_audio = gr.Audio(
                        label="Preview",
                        type="filepath",
                        interactive=False,
                    )
                with gr.Column(scale=2):
                    lib_selected_name = gr.Markdown("")
                    gr.Markdown("**Rating**")
                    lib_rating = gr.Radio(
                        choices=_RATING_CHOICES,
                        value=None,
                        label="",
                        container=False,
                    )
                    with gr.Row():
                        lib_delete_btn = gr.Button("🗑️ Delete", variant="stop", scale=1)
                    lib_status = gr.Markdown("")

            with gr.Accordion("Generation Details", open=True):
                lib_caption = gr.Textbox(label="Caption", interactive=False, lines=3)
                with gr.Row():
                    lib_bpm_field  = gr.Textbox(label="BPM",      interactive=False, scale=1, visible=False)
                    lib_key_field  = gr.Textbox(label="Key",       interactive=False, scale=1)
                    lib_seed_field = gr.Textbox(label="Seed",      interactive=False, scale=1)
                    lib_dur_field  = gr.Textbox(label="Duration",  interactive=False, scale=1)
                lib_lyrics = gr.Textbox(label="Lyrics", interactive=False, lines=12, max_lines=50)

        # State: path of the currently selected audio file
        lib_selected_path = gr.State(None)

    # ── Event wiring ─────────────────────────────────────────────────────────

    # Refresh / Sort / Filter
    for trigger in [lib_refresh_btn, lib_sort, lib_filter]:
        trigger.click(
            fn=do_refresh,
            inputs=[lib_sort, lib_filter],
            outputs=[lib_table, lib_songs_state, lib_count],
        ) if trigger is lib_refresh_btn else trigger.change(
            fn=do_refresh,
            inputs=[lib_sort, lib_filter],
            outputs=[lib_table, lib_songs_state, lib_count],
        )

    # Rating change → auto-save (.input so programmatic updates from select_song don't re-scan).
    # Declared before lib_table.select so the event reference can be passed to cancels=[].
    rating_save_evt = lib_rating.input(
        fn=save_rating,
        inputs=[lib_selected_path, lib_rating, lib_songs_state, lib_sort, lib_filter],
        outputs=[lib_table, lib_songs_state, lib_count, lib_status],
    )

    # Row select — cancels any in-flight rating_save_evt so the next song loads immediately.
    # When select_song outputs a new value to lib_rating the Radio fires its .input event,
    # which queues save_rating and blocks the next row-click.  cancels= preempts that.
    lib_table.select(
        fn=select_song,
        inputs=[lib_songs_state, lib_sort, lib_filter],
        outputs=[
            lib_selected_panel,
            lib_audio,
            lib_selected_name,
            lib_rating,
            lib_status,
            lib_caption,
            lib_bpm_field,
            lib_key_field,
            lib_seed_field,
            lib_dur_field,
            lib_lyrics,
            lib_selected_path,
        ],
        cancels=[rating_save_evt],
    )

    # Delete — also cancels rating_save_evt for the same reason as lib_table.select above.
    lib_delete_btn.click(
        fn=delete,
        inputs=[lib_selected_path, lib_sort, lib_filter],
        cancels=[rating_save_evt],
        outputs=[
            lib_table,
            lib_songs_state,
            lib_count,
            lib_selected_panel,
            lib_audio,
            lib_selected_name,
            lib_rating,
            lib_status,
            lib_caption,
            lib_bpm_field,
            lib_key_field,
            lib_seed_field,
            lib_dur_field,
            lib_lyrics,
            lib_selected_path,
        ],
    )

    return {
        "lib_refresh_btn":    lib_refresh_btn,
        "lib_sort":           lib_sort,
        "lib_filter":         lib_filter,
        "lib_count":          lib_count,
        "lib_table":          lib_table,
        "lib_songs_state":    lib_songs_state,
        "lib_selected_panel": lib_selected_panel,
        "lib_audio":          lib_audio,
        "lib_selected_name":  lib_selected_name,
        "lib_rating":         lib_rating,
        "lib_delete_btn":     lib_delete_btn,
        "lib_status":         lib_status,
        "lib_caption":        lib_caption,
        "lib_bpm_field":      lib_bpm_field,
        "lib_key_field":      lib_key_field,
        "lib_seed_field":     lib_seed_field,
        "lib_dur_field":      lib_dur_field,
        "lib_lyrics":         lib_lyrics,
        "lib_selected_path":  lib_selected_path,
    }

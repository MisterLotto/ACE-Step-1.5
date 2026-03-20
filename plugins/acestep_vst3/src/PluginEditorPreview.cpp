#include "PluginEditor.h"

#include "PluginProcessor.h"

namespace acestep::vst3
{
void ACEStepVST3AudioProcessorEditor::choosePreviewFile()
{
    juce::FileChooser chooser("Select preview audio file",
                              {},
                              "*.wav;*.aiff;*.flac;*.ogg;*.mp3");
    if (!chooser.browseForFileToOpen())
    {
        return;
    }

    processor_.stopPreview();
    processor_.loadPreviewFile(chooser.getResult());
    refreshStatusViews();
}

void ACEStepVST3AudioProcessorEditor::playPreviewFile()
{
    processor_.playPreview();
    refreshStatusViews();
}

void ACEStepVST3AudioProcessorEditor::stopPreviewFile()
{
    processor_.stopPreview();
    refreshStatusViews();
}

void ACEStepVST3AudioProcessorEditor::clearPreviewFile()
{
    processor_.stopPreview();
    processor_.clearPreviewFile();
    refreshStatusViews();
}

void ACEStepVST3AudioProcessorEditor::revealPreviewFile()
{
    processor_.revealPreviewFile();
}
}  // namespace acestep::vst3

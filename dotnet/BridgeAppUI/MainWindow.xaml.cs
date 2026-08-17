using Microsoft.Win32;
using System.Diagnostics;
using System.IO;
using System.Text;
using System.Windows;
using System.Windows.Controls;

namespace BridgeAppUI;

public partial class MainWindow : Window
{
    public MainWindow()
    {
        InitializeComponent();
    }

    private async void GenerateInputFile_Click(object sender, RoutedEventArgs e)
    {
        var outputDialog = new SaveFileDialog
        {
            Title = "Save generated input",
            Filter = "CSV file (*.csv)|*.csv",
            DefaultExt = ".csv",
            AddExtension = true,
            FileName = $"input_{DateTime.Now:yyyyMMdd_HHmmss}.csv"
        };

        if (outputDialog.ShowDialog() != true)
            return;

        try
        {
            GenerateInputFileButton.IsEnabled = false;
            InputBuilderStatusText.Text = "Generating input...";

            var projectRoot = FindProjectRoot();
            var configPath = SaveGeneratedConfiguration(projectRoot);

            var result = await RunInputGenerationAsync(
                configPath,
                outputDialog.FileName);

            if (result.ExitCode != 0)
            {
                throw new InvalidOperationException(
                    string.IsNullOrWhiteSpace(result.Error)
                        ? $"Python generator exited with code {result.ExitCode}."
                        : result.Error.Trim());
            }

            var outputPath = ReadGeneratedInputPath(result.Output);

            InputBuilderStatusText.Text = "Input generation completed";

            MessageBox.Show(
                $"Input generated to:\n{outputPath}\n\nConfiguration saved to:\n{configPath}",
                "Input generation",
                MessageBoxButton.OK,
                MessageBoxImage.Information);
        }
        catch (Exception exception)
        {
            InputBuilderStatusText.Text = "Input generation failed";

            MessageBox.Show(
                exception.Message,
                "Could not generate input",
                MessageBoxButton.OK,
                MessageBoxImage.Error);
        }
        finally
        {
            GenerateInputFileButton.IsEnabled = true;
        }
    }

    private string SaveGeneratedConfiguration(string projectRoot)
    {
        var configDirectory = Path.Combine(
            projectRoot,
            "python",
            "model_inputs",
            "generated_configs");

        Directory.CreateDirectory(configDirectory);

        var configPath = Path.Combine(
            configDirectory,
            $"bridge_input_{DateTime.Now:yyyyMMdd_HHmmss}.txt");

        File.WriteAllText(
            configPath,
            BuildInputConfiguration(),
            new UTF8Encoding(false));

        return configPath;
    }

    private async Task<PythonRunResult> RunInputGenerationAsync(
        string configPath,
        string outputPath)
    {
        var projectRoot = FindProjectRoot();
        var scriptPath = Path.Combine(
            projectRoot,
            "python",
            "main_generate_inputs.py");

        if (!File.Exists(scriptPath))
        {
            throw new FileNotFoundException(
                "Could not find python/main_generate_inputs.py.",
                scriptPath);
        }

        Exception? lastStartException = null;

        foreach (var pythonExecutable in new[] { "python", "py" })
        {
            try
            {
                using var process = new Process
                {
                    StartInfo = CreatePythonStartInfo(
                        pythonExecutable,
                        projectRoot,
                        scriptPath,
                        configPath,
                        outputPath)
                };

                process.Start();

                var outputTask = process.StandardOutput.ReadToEndAsync();
                var errorTask = process.StandardError.ReadToEndAsync();

                await process.WaitForExitAsync();

                return new PythonRunResult(
                    process.ExitCode,
                    await outputTask,
                    await errorTask);
            }
            catch (System.ComponentModel.Win32Exception exception)
            {
                lastStartException = exception;
            }
        }

        throw new InvalidOperationException(
            "Python was not found. Add Python to PATH or configure the interpreter.",
            lastStartException);
    }

    private static ProcessStartInfo CreatePythonStartInfo(
        string pythonExecutable,
        string projectRoot,
        string scriptPath,
        string configPath,
        string outputPath)
    {
        var startInfo = new ProcessStartInfo
        {
            FileName = pythonExecutable,
            WorkingDirectory = projectRoot,
            UseShellExecute = false,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            CreateNoWindow = true
        };

        startInfo.ArgumentList.Add(scriptPath);
        startInfo.ArgumentList.Add("--config");
        startInfo.ArgumentList.Add(configPath);
        startInfo.ArgumentList.Add("--output");
        startInfo.ArgumentList.Add(outputPath);

        return startInfo;
    }

    private static string FindProjectRoot()
    {
        DirectoryInfo? directory = new(AppContext.BaseDirectory);

        while (directory is not null)
        {
            var pythonDirectory = Path.Combine(directory.FullName, "python");
            var dotnetDirectory = Path.Combine(directory.FullName, "dotnet");

            if (Directory.Exists(pythonDirectory) && Directory.Exists(dotnetDirectory))
                return directory.FullName;

            directory = directory.Parent;
        }

        throw new DirectoryNotFoundException(
            "Could not locate the bridge-optimization-lab project root.");
    }

    private static string ReadGeneratedInputPath(string output)
    {
        const string marker = "GENERATED_INPUT_PATH=";

        return output
            .Split(new[] { '\r', '\n' }, StringSplitOptions.RemoveEmptyEntries)
            .FirstOrDefault(line => line.StartsWith(marker, StringComparison.Ordinal))?
            .Substring(marker.Length)
            .Trim()
            ?? string.Empty;
    }

    private sealed record PythonRunResult(
        int ExitCode,
        string Output,
        string Error);

    private string BuildInputConfiguration()
    {
        var builder = new StringBuilder();

        builder.AppendLine("# Bridge input configuration");
        builder.AppendLine($"# Generated: {DateTime.Now:yyyy-MM-dd HH:mm:ss}");
        builder.AppendLine();

        builder.AppendLine("[RUN]");
        builder.AppendLine($"n_models={GetNumberOfModels()}");
        builder.AppendLine("random_seed=None");
        builder.AppendLine();

        AppendGeometrySettings(builder);
        AppendLoadSettings(builder);
        AppendSupportSettings(builder);
        AppendTendonSettings(builder);
        AppendMaterialAndSectionSettings(builder);

        return builder.ToString();
    }

    private void AppendGeometrySettings(StringBuilder builder)
    {
        builder.AppendLine("[GEOMETRY]");

        AppendRange(
            builder,
            "n_spans",
            "-",
            NSpansModeTab,
            NSpansFixedTextBox,
            NSpansFromTextBox,
            NSpansToTextBox);

        AppendRange(
            builder,
            "span_length_m",
            "m",
            SpanLengthModeTab,
            SpanLengthFixedTextBox,
            SpanLengthFromTextBox,
            SpanLengthToTextBox);

        AppendRange(
            builder,
            "beam_height_m",
            "m",
            BeamHeightModeTab,
            BeamHeightFixedTextBox,
            BeamHeightFromTextBox,
            BeamHeightToTextBox);

        AppendRange(
            builder,
            "beam_width_m",
            "m",
            BeamWidthModeTab,
            BeamWidthFixedTextBox,
            BeamWidthFromTextBox,
            BeamWidthToTextBox);

        builder.AppendLine();
    }

    private void AppendLoadSettings(StringBuilder builder)
    {
        builder.AppendLine("[LOADS]");

        AppendRange(
            builder,
            "udl_kn_per_m",
            "kN/m",
            UdlModeTab,
            UdlFixedTextBox,
            UdlFromTextBox,
            UdlToTextBox);

        AppendEnumRange(
            builder,
            "udl_load_type",
            UdlDistributionModeTab,
            UdlDistributionFixedComboBox,
            UdlDistributionFromComboBox,
            UdlDistributionToComboBox);

        AppendText(builder, "self_weight_case", SelfWeightCaseTextBox);
        AppendText(builder, "udl_case", UdlCaseTextBox);
        AppendText(builder, "prestress_case", PrestressCaseTextBox);

        builder.AppendLine();
    }

    private void AppendSupportSettings(StringBuilder builder)
    {
        builder.AppendLine("[SUPPORTS]");

        AppendText(builder, "left_support", LeftSupportTextBox);
        AppendText(builder, "internal_support", InternalSupportTextBox);
        AppendText(builder, "right_support", RightSupportTextBox);

        builder.AppendLine();
    }

    private void AppendTendonSettings(StringBuilder builder)
    {
        builder.AppendLine("[TENDON]");

        AppendRange(
            builder,
            "n_tendons",
            "-",
            NTendonsModeTab,
            NTendonsFixedTextBox,
            NTendonsFromTextBox,
            NTendonsToTextBox);

        AppendRange(
            builder,
            "tendon_force_kn",
            "kN/tendon",
            TendonForceModeTab,
            TendonForceFixedTextBox,
            TendonForceFromTextBox,
            TendonForceToTextBox);

        AppendRange(
            builder,
            "tendon_area_mm2",
            "mm2/tendon",
            TendonAreaModeTab,
            TendonAreaFixedTextBox,
            TendonAreaFromTextBox,
            TendonAreaToTextBox);

        AppendRange(
            builder,
            "tendon_cover_m",
            "m",
            TendonCoverModeTab,
            TendonCoverFixedTextBox,
            TendonCoverFromTextBox,
            TendonCoverToTextBox);

        AppendText(
            builder,
            "tendon_control_points_per_span",
            TendonControlPointsTextBox);

        AppendEnumRange(
            builder,
            "tendon_shape_type",
            TendonShapeModeTab,
            TendonShapeFixedComboBox,
            TendonShapeFromComboBox,
            TendonShapeToComboBox);

        builder.AppendLine();
    }

    private void AppendMaterialAndSectionSettings(StringBuilder builder)
    {
        builder.AppendLine("[MATERIALS_AND_SECTION]");

        AppendText(builder, "concrete_material_name", ConcreteMaterialNameTextBox);
        AppendText(builder, "concrete_material_code", ConcreteMaterialCodeTextBox);
        AppendText(builder, "concrete_material_grade", ConcreteMaterialGradeTextBox);

        AppendText(builder, "tendon_material_name", TendonMaterialNameTextBox);
        AppendText(builder, "tendon_material_code", TendonMaterialCodeTextBox);
        AppendText(builder, "tendon_material_grade", TendonMaterialGradeTextBox);
        AppendText(builder, "tendon_material_id", TendonMaterialIdTextBox);

        AppendText(builder, "section_name", SectionNameTextBox);
        AppendText(builder, "section_id", SectionIdTextBox);

        builder.AppendLine($"outer_polygon={ReadComboBox(OuterPolygonComboBox)}");
        AppendText(builder, "inner_polygons", InnerPolygonsTextBox);

        builder.AppendLine();
    }

    private static void AppendRange(
        StringBuilder builder,
        string propertyName,
        string unit,
        TabControl modeTab,
        TextBox fixedTextBox,
        TextBox fromTextBox,
        TextBox toTextBox)
    {
        var isFixed = modeTab.SelectedIndex == 0;

        builder.AppendLine($"{propertyName}.mode={(isFixed ? "fixed" : "random")}");
        builder.AppendLine($"{propertyName}.unit={unit}");

        if (isFixed)
        {
            builder.AppendLine($"{propertyName}.value={fixedTextBox.Text.Trim()}");
            return;
        }

        builder.AppendLine($"{propertyName}.from={fromTextBox.Text.Trim()}");
        builder.AppendLine($"{propertyName}.to={toTextBox.Text.Trim()}");
    }

    private static void AppendEnumRange(
        StringBuilder builder,
        string propertyName,
        TabControl modeTab,
        ComboBox fixedComboBox,
        ComboBox fromComboBox,
        ComboBox toComboBox)
    {
        var isFixed = modeTab.SelectedIndex == 0;

        builder.AppendLine($"{propertyName}.mode={(isFixed ? "fixed" : "random")}");

        if (isFixed)
        {
            builder.AppendLine(
                $"{propertyName}.value={ReadComboBox(fixedComboBox)}");
            return;
        }

        builder.AppendLine(
            $"{propertyName}.from={ReadComboBox(fromComboBox)}");
        builder.AppendLine(
            $"{propertyName}.to={ReadComboBox(toComboBox)}");
    }

    private static void AppendText(
        StringBuilder builder,
        string propertyName,
        TextBox textBox)
    {
        builder.AppendLine($"{propertyName}={textBox.Text.Trim()}");
    }

    private static string ReadComboBox(ComboBox comboBox)
    {
        if (comboBox.SelectedItem is ComboBoxItem selectedItem)
            return selectedItem.Content?.ToString()?.Trim() ?? string.Empty;

        return comboBox.Text.Trim();
    }

    private int GetNumberOfModels()
{
    if (!int.TryParse(
            NumberOfModelsTextBox.Text.Trim(),
            out var numberOfModels) ||
        numberOfModels <= 0)
    {
        throw new InvalidOperationException(
            "Number of models must be a positive integer.");
    }

    return numberOfModels;
}
}
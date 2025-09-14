Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# Create form
$form = New-Object System.Windows.Forms.Form
$form.FormBorderStyle = [System.Windows.Forms.FormBorderStyle]::None
$form.WindowState = [System.Windows.Forms.FormWindowState]::Normal
$form.StartPosition = [System.Windows.Forms.FormStartPosition]::Manual
$form.Location = New-Object System.Drawing.Point(1300, 110)
$form.Size = New-Object System.Drawing.Size(50, 1)
$form.BackColor = [System.Drawing.Color]::Black
$form.Opacity = 0.6
$form.TopMost = $false
$form.ShowInTaskbar = $false

# Create label
$label = New-Object System.Windows.Forms.Label
$label.Location = New-Object System.Drawing.Point(10, 10)
$label.Size = New-Object System.Drawing.Size(280, 180)
$label.Font = New-Object System.Drawing.Font("Consolas", 11)
$label.ForeColor = [System.Drawing.Color]::White
$label.BackColor = [System.Drawing.Color]::Transparent
$form.Controls.Add($label)

# Timer for updates
$timer = New-Object System.Windows.Forms.Timer
$timer.Interval = 1000
$timer.Add_Tick({
    try {
        $content = Get-Content "D:\Code\Python\Projects\toph-submissions\data\progress.json" -Raw
        $json = $content | ConvertFrom-Json
        $label.Text = "Toph: " + $json.last_processed
    } catch {
        $label.Text = "Error reading file"
    }
})

$timer.Start()
$form.Show()

# Keep running
while ($form.Created) {
    [System.Windows.Forms.Application]::DoEvents()
    Start-Sleep -Milliseconds 100
}
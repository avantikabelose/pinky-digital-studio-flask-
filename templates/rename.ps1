$files = @(
    "templates\base.html",
    "templates\index.html", 
    "templates\gallery.html",
    "templates\booking.html",
    "templates\contact.html",
    "templates\dashboard.html"
)

foreach ($file in $files) {
    if (Test-Path $file) {
        (Get-Content $file) -replace 'ElitePhoto Studio', 'Pinky Digital Studio' | Set-Content $file
        Write-Host "Updated: $file"
    }
}

Write-Host "All files updated successfully!"
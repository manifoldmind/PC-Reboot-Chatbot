"""
OARM (Office Autosave & Reboot Module).
Содержит PowerShell-скрипт для безопасного сохранения документов Office перед перезагрузкой.
"""

OARM_SCRIPT = r"""
$ErrorActionPreference = 'Continue'
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$docs = [Environment]::GetFolderPath('MyDocuments')
if (-not $docs) { $docs = Join-Path $env:USERPROFILE 'Documents' }
$saveRoot = Join-Path $docs 'OARM_Autosave'
New-Item -ItemType Directory -Path $saveRoot -Force | Out-Null

function Get-Com([string[]]$ids) {
  foreach ($id in $ids) {
    try { return [Runtime.InteropServices.Marshal]::GetActiveObject($id) } catch {}
  }
  $null
}
function Has-Path([string]$p) {
  if ([string]::IsNullOrWhiteSpace($p)) { return $false }
  return ($p -match '^[A-Za-z]:\\' -or $p -match '^\\\\[^\\]+\\')
}
function StampPath($kind, $ext, $i) {
  Join-Path $saveRoot ("OARM_{0}_{1}_{2}{3}" -f $stamp, $kind, $i, $ext)
}

# Word
$word = Get-Com @('Word.Application','Word.Application.16','Word.Application.15')
if ($word) {
  try { $word.DisplayAlerts = 0 } catch {}
  for ($i = 1; $i -le [int]$word.Documents.Count; $i++) {
    $doc = $word.Documents.Item($i)
    $full = ''; try { $full = [string]$doc.FullName } catch {}
    if (Has-Path $full) { $doc.Save() }
    else {
      $p = StampPath 'Word' '.docx' $i
      try { $doc.SaveAs2([string]$p, 16) } catch { try { $doc.SaveAs([string]$p) } catch {} }
    }
  }
}

# Excel
$excel = Get-Com @('Excel.Application','Excel.Application.16','Excel.Application.15')
if ($excel) {
  try { $excel.DisplayAlerts = $false } catch {}
  for ($i = 1; $i -le [int]$excel.Workbooks.Count; $i++) {
    $wb = $excel.Workbooks.Item($i)
    $pathProp = ''; try { $pathProp = [string]$wb.Path } catch {}
    if ($pathProp) { $wb.Save() }
    else {
      $p = StampPath 'Excel' '.xlsx' $i
      try { $wb.SaveAs([string]$p, 51) } catch { try { $wb.SaveAs([string]$p) } catch {} }
    }
  }
}

# PowerPoint
$ppt = Get-Com @('PowerPoint.Application','PowerPoint.Application.16','PowerPoint.Application.15')
if ($ppt) {
  for ($i = 1; $i -le [int]$ppt.Presentations.Count; $i++) {
    $pres = $ppt.Presentations.Item($i)
    $pathProp = ''; try { $pathProp = [string]$pres.Path } catch {}
    if ($pathProp) { $pres.Save() }
    else {
      $p = StampPath 'PPT' '.pptx' $i
      try { $pres.SaveAs([string]$p, 24) } catch { try { $pres.SaveAs([string]$p) } catch {} }
    }
  }
}

# Outlook: незакрытые письма -> Черновики
$ol = Get-Com @('Outlook.Application','Outlook.Application.16','Outlook.Application.15')
if ($ol) {
  foreach ($insp in @($ol.Inspectors)) {
    try {
      $item = $insp.CurrentItem
      if ($null -eq $item) { continue }
      $cls = -1; try { $cls = [int]$item.Class } catch {}
      $sent = $false; try { $sent = [bool]$item.Sent } catch {}
      if ($cls -eq 43 -and -not $sent) {
        $drafts = $ol.Session.GetDefaultFolder(16)
        $item.Save()
        try { $null = $item.Move($drafts) } catch {}
      } else { try { $item.Save() } catch {} }
    } catch {}
  }
}

Write-Host "Autosave done -> $saveRoot"
Start-Sleep -Seconds 2
Restart-Computer -Force
"""

def get_oarm_script() -> str:
    """Возвращает текст PowerShell-скрипта OARM."""
    return OARM_SCRIPT
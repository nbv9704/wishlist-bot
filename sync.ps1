# Script auto-sync để commit và push code lên GitHub

# Đặt thư mục làm việc là thư mục dự án
Set-Location -Path "D:\wishlist"

# Vòng lặp vô hạn để kiểm tra thay đổi
while ($true) {
    # Kiểm tra xem có thay đổi nào không
    $status = git status --porcelain
    if ($status) {
        Write-Host "Thay doi duoc phat hien. Bat dau dong bo..."

        # Stage tất cả thay đổi
        git add .

        # Commit với thông điệp tự động
        $commitMessage = "Auto-sync: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
        git commit -m $commitMessage

        # Push lên GitHub
        git push origin main

        Write-Host "Da dong bo len GitHub thanh cong: $commitMessage"
    } else {
        Write-Host "Khong co thay doi moi. Kiem tra lai sau 5 phut..."
    }

    # Chờ 5 phút (300 giây) trước khi kiểm tra lại
    Start-Sleep -Seconds 60
}
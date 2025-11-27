// File: templates/js/script.js

console.log("Script đã được tải thành công!"); // Dòng này để kiểm tra F12

function showContent(panelId) {
    console.log("Bạn vừa bấm vào menu:", panelId);

    // 1. Ẩn tất cả các nội dung đang hiện (tìm các thẻ có class 'content-panel')
    const allPanels = document.querySelectorAll('.content-panel');
    allPanels.forEach(panel => {
        panel.classList.add('hidden'); // Thêm class hidden để ẩn đi
    });

    // 2. Hiện nội dung được chọn (tìm thẻ có id khớp với panelId)
    const targetPanel = document.getElementById(panelId);
    if (targetPanel) {
        targetPanel.classList.remove('hidden'); // Xóa class hidden để hiện lên
    } else {
        console.error("LỖI: Không tìm thấy nội dung có ID là:", panelId);
    }

    // 3. (Tùy chọn) Đổi màu menu để biết đang chọn cái nào
    // Xóa active cũ
    document.querySelectorAll('.menu-item').forEach(btn => {
        btn.classList.remove('bg-blue-800', 'border-l-4', 'border-blue-400');
    });
    
    // Thêm active mới
    const activeBtn = document.getElementById('menu-' + panelId);
    if (activeBtn) {
        activeBtn.classList.add('bg-blue-800', 'border-l-4', 'border-blue-400');
    }
}

// Mặc định khi vào trang sẽ mở tab đầu tiên
document.addEventListener("DOMContentLoaded", function() {
    const firstPanel = document.getElementById("curriculum");
    if (firstPanel) {
        firstPanel.classList.remove("hidden");
    }
});
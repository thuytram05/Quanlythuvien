function muonSach(id, tenSach) {
    // Hiệu ứng đổi màu nút khi bấm
    const btn = event.target;
    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>...';

    fetch('/api/muon-sach', {
        method: 'post',
        body: JSON.stringify({
            'id': id,
            'ten_sach': tenSach
        }),
        headers: {
            'Content-Type': 'application/json'
        }
    }).then(res => res.json()).then(data => {
        btn.disabled = false;
        btn.innerHTML = originalText;

        if (data.status === 'error') {
            Swal.fire({
                icon: 'error',
                title: 'Lỗi rồi!',
                text: data.msg
            });
        } else {
            // Thông báo thành công kiểu Toast (hiện ở góc màn hình)
            Swal.fire({
                icon: 'success',
                title: data.msg,
                toast: true,
                position: 'top-end',
                showConfirmButton: false,
                timer: 2000
            });

            // Cập nhật số lượng trên badge
            let counter = document.querySelector('.cart-counter');
            if (counter) {
                counter.innerText = data.total_quantity + " / 5";
                // Thêm hiệu ứng rung cho badge
                counter.classList.add('animate__animated', 'animate__bounceIn');
                setTimeout(() => counter.classList.remove('animate__animated', 'animate__bounceIn'), 1000);
            }
        }
    }).catch(err => {
        btn.disabled = false;
        btn.innerHTML = originalText;
        console.error(err);
    });
}

// Hàm xác nhận mượn chính thức trong trang phieu_muon.html
function xacNhanMuon() {
    Swal.fire({
        title: 'Xác nhận mượn?',
        text: "Bạn có chắc chắn muốn lập phiếu mượn này không?",
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#d33',
        confirmButtonText: 'Đồng ý',
        cancelButtonText: 'Hủy'
    }).then((result) => {
        if (result.isConfirmed) {
            fetch('/api/xac-nhan-muon', {
                method: 'post',
                headers: { 'Content-Type': 'application/json' }
            }).then(res => res.json()).then(data => {
                if (data.status === 'success') {
                    Swal.fire('Thành công!', data.msg, 'success').then(() => {
                        location.href = '/'; // Mượn xong đẩy về trang chủ
                    });
                } else {
                    Swal.fire('Thất bại', data.msg, 'error');
                }
            });
        }
    });
}
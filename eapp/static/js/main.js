
const updateCartBadge = (stats) => {
    const counters = document.querySelectorAll('.cart-counter');
    counters.forEach(counter => {
        if (counter) {
            counter.innerText = stats.total_quantity;
            counter.classList.remove('animate__bounceIn');
            void counter.offsetWidth;
            counter.classList.add('animate__animated', 'animate__bounceIn');
        }
    });
};

async function muonSach(id, name) {
    const btn = event.currentTarget;
    const originalContent = btn.innerHTML;

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';

    try {
        const response = await fetch('/api/cart', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ "id": id, "name": name })
        });

        const data = await response.json();

        if (response.status === 200) {
            const Toast = Swal.mixin({
                toast: true,
                position: 'top-end',
                showConfirmButton: false,
                timer: 2500,
                timerProgressBar: true
            });

            Toast.fire({
                icon: 'success',
                title: `Đã thêm cuốn "${name}"`
            });

            updateCartBadge(data);
        } else {
            Swal.fire({
                icon: 'warning',
                title: 'Thông báo',
                text: data.err_msg,
                confirmButtonColor: '#3d2b1f'
            });
        }
    } catch (err) {
        console.error("Lỗi kết nối:", err);
        Swal.fire('Lỗi', 'Không thể kết nối với máy chủ!', 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalContent;
    }
}

async function removeItem(bookId) {
    const result = await Swal.fire({
        title: 'Bỏ mượn cuốn này?',
        icon: 'question',
        showCancelButton: true,
        confirmButtonText: 'Đồng ý',
        cancelButtonText: 'Hủy'
    });

    if (result.isConfirmed) {
        try {
            const res = await fetch(`/api/cart/${bookId}`, { method: 'DELETE' });
            const data = await res.json();
            updateCartBadge(data);
            location.reload();
        } catch (err) {
            Swal.fire('Lỗi', 'Không thể xóa mục này', 'error');
        }
    }
}

function xacNhanMuon() {
    Swal.fire({
        title: '<h3 class="fw-black">Thông tin mượn sách</h3>',
        html: `
            <div class="text-start">
                <label class="small fw-bold text-uppercase">Số điện thoại nhận sách</label>
                <input type="text" id="phone" class="swal2-input m-0 w-100 mb-3" placeholder="Nhập SĐT của bạn...">

                <label class="small fw-bold text-uppercase">Ngày dự kiến trả</label>
                <input type="date" id="returnDate" class="swal2-input m-0 w-100 mb-3">

                <label class="small fw-bold text-uppercase">Ghi chú thêm</label>
                <textarea id="note" class="swal2-textarea m-0 w-100" placeholder="Lời nhắn cho thủ thư..."></textarea>
            </div>
        `,
        showCancelButton: true,
        confirmButtonText: 'LẬP PHIẾU MƯỢN',
        confirmButtonColor: '#3d2b1f',
        preConfirm: () => {
            const phone = document.getElementById('phone').value;
            const returnDate = document.getElementById('returnDate').value;
            if (!phone || !returnDate) {
                Swal.showValidationMessage('Vui lòng nhập đầy đủ SĐT và Ngày trả!');
            }
            return {
                phone: phone,
                returnDate: returnDate,
                note: document.getElementById('note').value
            };
        }
    }).then(async (result) => {
        if (result.isConfirmed) {
            try {
                Swal.fire({ title: 'Đang xử lý...', allowOutsideClick: false, didOpen: () => Swal.showLoading() });

                const response = await fetch('/api/pay', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(result.value)
                });

                const data = await response.json();

                if (data.status === 200) {
                    Swal.fire({
                        icon: 'success',
                        title: 'Thành công!',
                        text: 'Phiếu mượn đã được lập. Vui lòng đến quầy nhận sách.',
                        confirmButtonColor: '#3d2b1f'
                    }).then(() => location.href = '/lich-su-muon');
                } else {
                    Swal.fire('Thất bại', data.err_msg, 'error');
                }
            } catch (err) {
                Swal.fire('Lỗi', 'Có lỗi xảy ra trong quá trình xử lý', 'error');
            }
        }
    });
}
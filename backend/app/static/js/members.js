/**
 * Member Management - Client-side functionality
 */

// Variables to track current operation
let currentMemberId = null;
const memberModals = {
    add: null,
    edit: null,
    delete: null
};

// Initialize modals
document.addEventListener('DOMContentLoaded', () => {
    memberModals.add = new bootstrap.Modal(document.getElementById('addMemberModal'));
    memberModals.edit = new bootstrap.Modal(document.getElementById('editMemberModal'));
    memberModals.delete = new bootstrap.Modal(document.getElementById('deleteMemberModal'));
});

/**
 * Open Add Member Modal
 */
function openAddMemberModal() {
    document.getElementById('addMemberForm').reset();
    memberModals.add.show();
}

/**
 * Submit Add Member Form
 */
function submitAddMember() {
    const name = document.getElementById('add_name')?.value.trim();
    const email = document.getElementById('add_email')?.value.trim();
    const phone = document.getElementById('add_phone')?.value.trim();

    // Validation
    if (!name) {
        showToast('Member name is required', 'warning');
        return;
    }

    if (email && !isValidEmail(email)) {
        showToast('Invalid email format', 'warning');
        return;
    }

    if (phone && !isValidPhone(phone)) {
        showToast('Invalid phone format', 'warning');
        return;
    }

    // Submit via AJAX
    const formData = { name, email: email || null, phone: phone || null };

    fetch('/members/add', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Member added successfully!', 'success');
            memberModals.add.hide();
            setTimeout(() => location.reload(), 1000);
        } else {
            showToast(data.error || 'Failed to add member', 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Error adding member: ' + error.message, 'danger');
    });
}

/**
 * Open Edit Member Modal
 */
function openEditMemberModal(memberId) {
    currentMemberId = memberId;

    // Fetch member data
    fetch(`/members/get/${memberId}`)
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const member = data.member;
            document.getElementById('edit_id').value = member.id;
            document.getElementById('edit_name').value = member.name;
            document.getElementById('edit_email').value = member.email || '';
            document.getElementById('edit_phone').value = member.phone || '';
            memberModals.edit.show();
        } else {
            showToast('Failed to load member data', 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Error loading member: ' + error.message, 'danger');
    });
}

/**
 * Submit Edit Member Form
 */
function submitEditMember() {
    const memberId = document.getElementById('edit_id')?.value;
    const name = document.getElementById('edit_name')?.value.trim();
    const email = document.getElementById('edit_email')?.value.trim();
    const phone = document.getElementById('edit_phone')?.value.trim();

    // Validation
    if (!name) {
        showToast('Member name is required', 'warning');
        return;
    }

    if (email && !isValidEmail(email)) {
        showToast('Invalid email format', 'warning');
        return;
    }

    if (phone && !isValidPhone(phone)) {
        showToast('Invalid phone format', 'warning');
        return;
    }

    const formData = { name, email: email || null, phone: phone || null };

    fetch(`/members/${memberId}/edit`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Member updated successfully!', 'success');
            memberModals.edit.hide();
            setTimeout(() => location.reload(), 1000);
        } else {
            showToast(data.error || 'Failed to update member', 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Error updating member: ' + error.message, 'danger');
    });
}

/**
 * Open Delete Member Modal
 */
function openDeleteMemberModal(memberId, memberName) {
    currentMemberId = memberId;
    document.getElementById('del_name').textContent = memberName;

    // Check if member is used in expenses
    fetch(`/members/${memberId}/expenses-count`)
    .then(response => response.json())
    .then(data => {
        const warningEl = document.getElementById('del_warning');
        const expensesEl = document.getElementById('del_expenses');
        if (data.count > 0) {
            warningEl.style.display = 'block';
            expensesEl.textContent = `This member is involved in ${data.count} expense(s). Deleting them may affect expense records.`;
        } else {
            warningEl.style.display = 'none';
        }
    })
    .catch(error => {
        console.warn('Could not load expense count:', error);
    });

    memberModals.delete.show();
}

/**
 * Submit Delete Member
 */
function submitDeleteMember() {
    if (!currentMemberId) return;

    fetch(`/members/${currentMemberId}/delete`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Member removed successfully!', 'success');
            memberModals.delete.hide();
            setTimeout(() => location.reload(), 1000);
        } else {
            showToast(data.error || 'Failed to remove member', 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Error removing member: ' + error.message, 'danger');
    });
}

/**
 * Email Validation
 */
function isValidEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

/**
 * Phone Validation
 */
function isValidPhone(phone) {
    // Accept various phone formats (10 digits optional with +, -, etc.)
    const re = /^[\d\s\-\+\(\)]{10,}$/;
    return re.test(phone.replace(/\s/g, ''));
}

/**
 * Format Currency (INR)
 */
function formatCurrencyINR(amount) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        minimumFractionDigits: 2
    }).format(amount);
}

/**
 * Calculate Member Balance
 */
function calculateBalance(totalPaid, totalShare) {
    return totalPaid - totalShare;
}

/**
 * Get Balance Status Color
 */
function getBalanceStatusColor(balance) {
    if (balance > 0) return 'text-success'; // member gets money back
    if (balance < 0) return 'text-warning'; // member owes money
    return 'text-muted'; // settled
}

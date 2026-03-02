/**
 * Expense Management - Client-side functionality
 */

// ===== CONSTANTS =====
const SPLITS = {
    EQUAL: 'equal',
    EXACT: 'exact',
    PERCENTAGE: 'percentage'
};

// ===== FORM WIZARD =====
let currentStep = 1;
const totalSteps = 3;

function goToStep(step) {
    // Validate current step before advancing
    if (step > currentStep && !validateCurrentStep()) {
        showToast('Please fill in all required fields correctly', 'warning');
        return;
    }

    currentStep = step;
    updateStepDisplay();
}

function validateCurrentStep() {
    switch (currentStep) {
        case 1:
            const description = document.getElementById('description')?.value.trim();
            const amount = parseFloat(document.getElementById('amount')?.value);
            const category = document.querySelector('input[name="category"]:checked');
            const expenseDate = document.getElementById('expense_date')?.value;

            if (!description) {
                showToast('Description is required', 'warning');
                return false;
            }
            if (!amount || amount <= 0) {
                showToast('Amount must be greater than 0', 'warning');
                return false;
            }
            if (!category) {
                showToast('Please select a category', 'warning');
                return false;
            }
            if (!expenseDate) {
                showToast('Date is required', 'warning');
                return false;
            }
            return true;

        case 2:
            const paidBy = document.getElementById('paid_by_member_id')?.value;
            if (!paidBy) {
                showToast('Please select who paid', 'warning');
                return false;
            }
            return true;

        case 3:
            // Will be validated on submit
            return true;

        default:
            return true;
    }
}

function updateStepDisplay() {
    // Hide all step divs
    document.querySelectorAll('[data-step]').forEach(el => {
        el.style.display = 'none';
    });

    // Show current step
    document.querySelector(`[data-step="${currentStep}"]`).style.display = 'block';

    // Update progress bar
    const progress = (currentStep / totalSteps) * 100;
    const progressBar = document.getElementById('progressBar');
    if (progressBar) {
        progressBar.style.width = progress + '%';
    }

    // Update step indicator text
    const stepIndicator = document.getElementById('stepIndicator');
    if (stepIndicator) {
        stepIndicator.textContent = `Step ${currentStep} of ${totalSteps}`;
    }

    // Update button states
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    const submitBtn = document.getElementById('submitBtn');

    if (prevBtn) prevBtn.style.display = currentStep === 1 ? 'none' : 'inline-block';
    if (nextBtn) nextBtn.style.display = currentStep === totalSteps ? 'none' : 'inline-block';
    if (submitBtn) submitBtn.style.display = currentStep === totalSteps ? 'inline-block' : 'none';
}

// ===== SPLIT CALCULATOR =====
function updateSplitPreview() {
    const amount = parseFloat(document.getElementById('amount')?.value) || 0;
    const splitType = document.querySelector('input[name="split_type"]:checked')?.value || SPLITS.EQUAL;
    const selectedMembers = document.querySelectorAll('input[name="split_members"]:checked');

    if (amount <= 0 || selectedMembers.length === 0) {
        document.getElementById('splitPreview').innerHTML = '<p class="text-muted">Select members to see split preview</p>';
        return;
    }

    let html = '<div class="list-group">';

    if (splitType === SPLITS.EQUAL) {
        const perMember = amount / selectedMembers.length;
        selectedMembers.forEach(input => {
            const memberName = input.dataset.memberName;
            html += `
                <div class="list-group-item d-flex justify-content-between align-items-center">
                    <span>${memberName}</span>
                    <strong class="text-success">₹${formatCurrency(perMember)}</strong>
                </div>
            `;
        });
    } else if (splitType === SPLITS.EXACT) {
        let total = 0;
        selectedMembers.forEach(input => {
            const memberId = input.value;
            const exactAmount = parseFloat(document.getElementById(`split_amount_${memberId}`)?.value) || 0;
            const memberName = input.dataset.memberName;
            total += exactAmount;

            html += `
                <div class="list-group-item d-flex justify-content-between align-items-center">
                    <span>${memberName}</span>
                    <strong class="text-success">₹${formatCurrency(exactAmount)}</strong>
                </div>
            `;
        });

        const remaining = amount - total;
        if (Math.abs(remaining) > 0.01) {
            html += `
                <div class="list-group-item bg-warning-transparent d-flex justify-content-between">
                    <span class="text-warning">Remaining</span>
                    <strong class="text-warning">₹${formatCurrency(remaining)}</strong>
                </div>
            `;
        }
    } else if (splitType === SPLITS.PERCENTAGE) {
        let totalPct = 0;
        selectedMembers.forEach(input => {
            const memberId = input.value;
            const pct = parseFloat(document.getElementById(`split_pct_${memberId}`)?.value) || 0;
            const memberName = input.dataset.memberName;
            const shareAmount = (amount * pct) / 100;
            totalPct += pct;

            html += `
                <div class="list-group-item d-flex justify-content-between align-items-center">
                    <span>${memberName} (${pct}%)</span>
                    <strong class="text-success">₹${formatCurrency(shareAmount)}</strong>
                </div>
            `;
        });

        if (Math.abs(totalPct - 100) > 0.01) {
            html += `
                <div class="list-group-item bg-warning-transparent d-flex justify-content-between">
                    <span class="text-warning">Total %</span>
                    <strong class="text-warning">${totalPct.toFixed(1)}%</strong>
                </div>
            `;
        }
    }

    html += '</div>';
    document.getElementById('splitPreview').innerHTML = html;
}

function distributeEqual() {
    const amount = parseFloat(document.getElementById('amount')?.value) || 0;
    const selectedMembers = document.querySelectorAll('input[name="split_members"]:checked');

    if (amount <= 0 || selectedMembers.length === 0) {
        showToast('Enter amount and select members', 'warning');
        return;
    }

    const perMember = amount / selectedMembers.length;

    selectedMembers.forEach(input => {
        const memberId = input.value;
        const input_exact = document.getElementById(`split_amount_${memberId}`);
        if (input_exact) {
            input_exact.value = perMember.toFixed(2);
        }
    });

    updateSplitPreview();
}

// ===== DATE PICKER SHORTCUTS =====
function initDatePicker() {
    const today = new Date();
    const todayStr = today.toISOString().split('T')[0];
    document.getElementById('expense_date').value = todayStr;

    // Shortcut buttons
    document.getElementById('dateShortcut_today')?.addEventListener('click', () => {
        document.getElementById('expense_date').value = todayStr;
    });

    document.getElementById('dateShortcut_yesterday')?.addEventListener('click', () => {
        const yesterday = new Date(today);
        yesterday.setDate(yesterday.getDate() - 1);
        document.getElementById('expense_date').value = yesterday.toISOString().split('T')[0];
    });

    document.getElementById('dateShortcut_lastweek')?.addEventListener('click', () => {
        const lastWeek = new Date(today);
        lastWeek.setDate(lastWeek.getDate() - 7);
        document.getElementById('expense_date').value = lastWeek.toISOString().split('T')[0];
    });
}

// ===== CATEGORY SELECTOR =====
function selectCategory(category) {
    document.querySelectorAll('.category-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.closest('.category-btn').classList.add('active');
    document.getElementById('category_hidden').value = category;
}

// ===== FORM SUBMISSION =====
function submitExpenseForm() {
    if (!validateCurrentStep()) {
        return;
    }

    // Validate splits
    const amount = parseFloat(document.getElementById('amount').value);
    const splitType = document.querySelector('input[name="split_type"]:checked').value;
    const selectedMembers = document.querySelectorAll('input[name="split_members"]:checked');

    if (selectedMembers.length === 0) {
        showToast('Select at least one member for split', 'warning');
        return;
    }

    let totalSplit = 0;
    if (splitType === SPLITS.EXACT) {
        selectedMembers.forEach(input => {
            const amt = parseFloat(document.getElementById(`split_amount_${input.value}`).value) || 0;
            totalSplit += amt;
        });
        if (Math.abs(totalSplit - amount) > 0.01) {
            showToast(`Split amounts must equal total (₹${amount.toFixed(2)})`, 'warning');
            return;
        }
    } else if (splitType === SPLITS.PERCENTAGE) {
        selectedMembers.forEach(input => {
            const pct = parseFloat(document.getElementById(`split_pct_${input.value}`).value) || 0;
            totalSplit += pct;
        });
        if (Math.abs(totalSplit - 100) > 0.01) {
            showToast(`Percentages must sum to 100% (got ${totalSplit.toFixed(1)}%)`, 'warning');
            return;
        }
    }

    // Submit form
    document.getElementById('expenseForm').submit();
}

// ===== INITIALIZE ON PAGE LOAD =====
document.addEventListener('DOMContentLoaded', () => {
    initDatePicker();
    updateStepDisplay();

    // Event listeners
    document.getElementById('amount')?.addEventListener('change', updateSplitPreview);
    document.getElementById('amount')?.addEventListener('input', updateSplitPreview);
    document.querySelectorAll('input[name="split_type"]').forEach(radio => {
        radio.addEventListener('change', updateSplitPreview);
    });
    document.querySelectorAll('input[name="split_members"]').forEach(checkbox => {
        checkbox.addEventListener('change', updateSplitPreview);
    });

    // Category buttons
    document.querySelectorAll('.category-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.category-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
        });
    });
});

// ===== FORMATTING UTILITIES =====
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        minimumFractionDigits: 2
    }).format(amount).replace('₹', '').trim();
}

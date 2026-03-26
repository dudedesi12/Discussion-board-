// Auto-dismiss flash messages
document.addEventListener('DOMContentLoaded', function () {
    setTimeout(() => {
        document.querySelectorAll('.alert.alert-dismissible').forEach(alert => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            bsAlert.close();
        });
    }, 5000);

    // Tag input helper
    const tagInput = document.querySelector('input[name="tags"]');
    if (tagInput) {
        tagInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                const val = this.value.trim();
                if (val && !val.endsWith(',')) this.value = val + ', ';
            }
        });
    }

    // Relative timestamps
    document.querySelectorAll('[data-timestamp]').forEach(el => {
        const ts = new Date(el.dataset.timestamp);
        const now = new Date();
        const diff = Math.floor((now - ts) / 1000);
        let text = '';
        if (diff < 60) text = 'just now';
        else if (diff < 3600) text = `${Math.floor(diff/60)}m ago`;
        else if (diff < 86400) text = `${Math.floor(diff/3600)}h ago`;
        else text = ts.toLocaleDateString();
        el.textContent = text;
    });
});

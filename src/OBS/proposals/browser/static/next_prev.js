$(document).ready(function () {
    // 1. Find Plone 6's native Mockup AutoTOC container
    var $autotocForm = $('.pat-autotoc');
    if (!$autotocForm.length) return;

    // 2. Listen to Plone's custom component initialization event
    $autotocForm.on('init.autotoc.patterns', function () {
        
        var $navContainer = $('.autotoc-nav');
        var $tabs = $navContainer.find('a');

        if (!$tabs.length) return; // Exit if no multi-fieldset tabs exist

        // Hide the top auto-generated tab navigation bar to look like a wizard
        $navContainer.addClass('d-none');

        // 3. Pinpoint native Plone form and action buttons
        var $form = $autotocForm.closest('form');
        var $saveBtn = $form.find('#form-buttons-save');

        if (!$saveBtn.length) return;

        // 4. Inject Next & Previous layout actions right next to the Save button
        $saveBtn.before('<button type="button" class="btn btn-secondary me-2" id="wizard-prev" style="display:none;">&laquo; Previous</button>');
        $saveBtn.before('<button type="button" class="btn btn-primary me-2" id="wizard-next">Next &raquo;</button>');

        var $prevBtn = $('#wizard-prev');
        var $nextBtn = $('#wizard-next');

        // 5. Layout Engine to toggle buttons vs steps
        function updateWizardUI() {
            var $activeTab = $navContainer.find('a.active');
            var activeIndex = $tabs.index($activeTab);

            // Toggle "Previous" visibility
            if (activeIndex === 0) {
                $prevBtn.hide();
            } else {
                $prevBtn.show();
            }

            // Toggle "Next" vs Plone's "Save" visibility
            if (activeIndex === $tabs.length - 1) {
                $nextBtn.hide();
                //$saveBtn.show(); // Reveal native save button on the final step
            } else {
                $nextBtn.show();
                //$saveBtn.hide(); // Keep save button hidden on early steps
            }
        }

        // Initialize display configuration right after injection
        updateWizardUI();

        // 6. Next Button Click Event with Validation Check
        $nextBtn.on('click', function (e) {
            e.preventDefault();
            
            var $activeTab = $navContainer.find('a.active');
            var activeIndex = $tabs.index($activeTab);
            
            // Map tabs to fieldset containers via hashes
            var targetPanelId = $activeTab.attr('href');
            var $currentPanel = $(targetPanelId);

            // Find inputs within the CURRENT step
            var $stepFields = $currentPanel.find('input, select, textarea');
            var isStepValid = true;

            // Validate fields loop using native browser API
            $stepFields.each(function () {
                if (!this.checkValidity()) {
                    isStepValid = false;
                    this.reportValidity(); // Highlight the problem field
                    return false; // Break loop
                }
            });

            if (!isStepValid) return; // Block step changes if invalid

            // Transition to next step
            var nextIndex = activeIndex + 1;
            if (nextIndex < $tabs.length) {
                $tabs.get(nextIndex).click(); 
                
                setTimeout(updateWizardUI, 30);
                window.scrollTo({ top: $form.offset().top - 60, behavior: 'smooth' });
            }
        });

        // 7. Previous Button Click Event (No validation needed)
        $prevBtn.on('click', function (e) {
            e.preventDefault();
            var $activeTab = $navContainer.find('a.active');
            var prevIndex = $tabs.index($activeTab) - 1;

            if (prevIndex >= 0) {
                $tabs.get(prevIndex).click();
                
                setTimeout(updateWizardUI, 30);
                window.scrollTo({ top: $form.offset().top - 60, behavior: 'smooth' });
            }
        });

        // FIXED ACTION: Explicit submit trigger on the Save button
        $saveBtn.on('click', function (e) {
            // Check if final step passes HTML5 validation before submitting
            var $activeTab = $navContainer.find('a.active');
            var targetPanelId = $activeTab.attr('href');
            var $currentPanel = $(targetPanelId);
            var $stepFields = $currentPanel.find('input, select, textarea');
            var isFinalStepValid = true;

            $stepFields.each(function () {
                if (!this.checkValidity()) {
                    isFinalStepValid = false;
                    this.reportValidity();
                    return false;
                }
            });

            if (!isFinalStepValid) {
                e.preventDefault();
                return false;
            }

            // If valid, explicitly tell the form node to fire its native request submit
            $form.attr('novalidate', 'novalidate'); // Turn off redundant full-form browser bubbles
            $form.trigger('submit'); 
        });
    });
});

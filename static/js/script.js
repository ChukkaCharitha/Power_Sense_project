/**
 * PowerSense — script.js
 * Form validation, UI effects, and interactive helpers using jQuery.
 */

$(document).ready(function () {

  /* ── AC Hours toggle ──────────────────────────────────────── */
  // Show/hide AC hours field depending on AC unit count
  function toggleAcHours() {
    const acUnits = parseInt($('#ac_units').val()) || 0;
    if (acUnits === 0) {
      $('#ac_hours').val(0);
      $('#acHoursGroup').addClass('opacity-50').find('input').prop('readonly', true);
    } else {
      $('#acHoursGroup').removeClass('opacity-50').find('input').prop('readonly', false);
    }
  }
  $('#ac_units').on('change', toggleAcHours);
  toggleAcHours(); // run on page load


  /* ── Range sliders for hours ──────────────────────────────── */
  // Add a live preview next to hour inputs
  function addLivePreview(inputId) {
    const $input = $('#' + inputId);
    if ($input.length && !$('#preview_' + inputId).length) {
      $input.after(
        `<small id="preview_${inputId}" class="text-muted ms-2"></small>`
      );
    }
    $input.on('input', function () {
      const val = parseFloat($(this).val());
      if (!isNaN(val)) {
        $('#preview_' + inputId).text(`= ${val} hrs/day`);
      } else {
        $('#preview_' + inputId).text('');
      }
    });
  }
  ['ac_hours', 'fan_hours', 'tv_hours'].forEach(addLivePreview);


  /* ── Form Validation ──────────────────────────────────────── */
  $('#predictForm').on('submit', function (e) {
    let valid = true;

    // Clear previous errors
    clearErrors();

    // Name
    const name = $('#name').val().trim();
    if (name.length < 2) {
      showError('nameError', '#name');
      valid = false;
    }

    // Members
    const members = parseInt($('#members').val());
    if (isNaN(members) || members < 1 || members > 12) {
      showError('membersError', '#members');
      valid = false;
    }

    // Season
    const season = $('#season').val();
    if (!season) {
      showError('seasonError', '#season');
      valid = false;
    }

    // AC hours (only if AC units > 0)
    const acUnits = parseInt($('#ac_units').val()) || 0;
    if (acUnits > 0) {
      const acHours = parseFloat($('#ac_hours').val());
      if (isNaN(acHours) || acHours < 0 || acHours > 24) {
        showError('acHoursError', '#ac_hours');
        valid = false;
      }
    }

    // Fan hours
    const fanHours = parseFloat($('#fan_hours').val());
    if (isNaN(fanHours) || fanHours < 0 || fanHours > 24) {
      showError('fanError', '#fan_hours');
      valid = false;
    }

    // TV hours
    const tvHours = parseFloat($('#tv_hours').val());
    if (isNaN(tvHours) || tvHours < 0 || tvHours > 20) {
      showError('tvError', '#tv_hours');
      valid = false;
    }

    // Washing uses
    const washingUses = parseInt($('#washing_uses').val());
    if (isNaN(washingUses) || washingUses < 0 || washingUses > 60) {
      showError('washingError', '#washing_uses');
      valid = false;
    }

    if (!valid) {
      e.preventDefault(); // stop form submission
      // Scroll to first error
      $('html, body').animate({
        scrollTop: $('.is-invalid:first').offset().top - 100
      }, 400);
      return false;
    }

    // Show loading state on button
    $('#submitBtn')
      .html('<span class="spinner-border spinner-border-sm me-2"></span>Predicting...')
      .prop('disabled', true);
  });


  /* ── Helpers ──────────────────────────────────────────────── */
  function showError(errorId, inputSelector) {
    $('#' + errorId).show();
    $(inputSelector).closest('.input-group').addClass('is-invalid');
    $(inputSelector).addClass('is-invalid');
  }

  function clearErrors() {
    $('.invalid-msg').hide();
    $('.is-invalid').removeClass('is-invalid');
  }

  // Live clear on input change
  $('input, select').on('input change', function () {
    $(this).removeClass('is-invalid');
    $(this).closest('.input-group').removeClass('is-invalid');
  });


  /* ── History delete confirm ───────────────────────────────── */
  window.confirmDelete = function (form) {
    return confirm('🗑️ Delete this prediction record?\nThis action cannot be undone.');
  };


  /* ── Navbar scroll effect ─────────────────────────────────── */
  $(window).on('scroll', function () {
    if ($(this).scrollTop() > 30) {
      $('#mainNav').addClass('shadow');
    } else {
      $('#mainNav').removeClass('shadow');
    }
  });


  /* ── Tooltip initialisation (Bootstrap 5) ─────────────────── */
  const tooltipEls = document.querySelectorAll('[data-bs-toggle="tooltip"]');
  tooltipEls.forEach(el => new bootstrap.Tooltip(el));


  /* ── Auto-dismiss alerts ──────────────────────────────────── */
  setTimeout(function () {
    $('.alert').fadeOut(500);
  }, 5000);

});

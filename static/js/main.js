$(document).ready(function() {
    // Gallery filtering
    $('.filter-btn').click(function() {
        const category = $(this).data('category');
        
        $('.filter-btn').removeClass('active');
        $(this).addClass('active');
        
        if (category === 'all') {
            $('.gallery-item').fadeIn();
        } else {
            $('.gallery-item').each(function() {
                if ($(this).data('category') === category) {
                    $(this).fadeIn();
                } else {
                    $(this).fadeOut();
                }
            });
        }
    });
    
    // Smooth scroll for anchor links
    $('a[href^="#"]').on('click', function(e) {
        e.preventDefault();
        const target = $(this.hash);
        if (target.length) {
            $('html, body').animate({
                scrollTop: target.offset().top - 70
            }, 800);
        }
    });
    
    // Navbar background change on scroll
    $(window).scroll(function() {
        if ($(window).scrollTop() > 50) {
            $('.navbar').css('padding', '10px 0');
        } else {
            $('.navbar').css('padding', '20px 0');
        }
    });
    
    // Form validation
    $('form').on('submit', function(e) {
        const required = $(this).find('[required]');
        let valid = true;
        
        required.each(function() {
            if (!$(this).val()) {
                $(this).addClass('is-invalid');
                valid = false;
            } else {
                $(this).removeClass('is-in
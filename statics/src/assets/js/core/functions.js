/*! functions.js | Adminuiux 2023-2024 */
"use strict";

import $ from 'jquery';
window.jQuery = $;
window.$ = $;

var body = $('body');

/* default window width */
var windowswidth = $(window).width();
$(window).on('resize', function () {
    windowswidth = $(window).width();
});

//Pageloader hide
function PageLoaderHide() {
    $('.pageloader').fadeOut();
    body.removeClass('overflow-hidden');
}
window.PageLoaderHide = PageLoaderHide;

// fixed header content space
function fixedHeaderSpace() {
    if ($('.adminuiux-header .navbar').hasClass('fixed-top') === true) {
        $('.adminuiux-sidebar').css('padding-top', $('.adminuiux-header .navbar').outerHeight());
        $('.adminuiux-content').css('padding-top', $('.adminuiux-header .navbar').outerHeight());
    }
}
window.fixedHeaderSpace = fixedHeaderSpace;

function fixedFooterSpace() {
    $(".adminuiux-mobile-footer").length > 0 && $("body").css("padding-bottom", $(".adminuiux-mobile-footer").outerHeight())
}
window.fixedFooterSpace = fixedFooterSpace;

function activeHeader() {
    if ($(window).scrollTop() > 30) {
        $('.adminuiux-header').addClass('active');
    } else {
        $('.adminuiux-header').removeClass('active');
    }
}
window.activeHeader = activeHeader;

// scrolling direction 

function scrolldirection() {
    var lastScrollTop = document.documentElement.scrollTop;

    window.addEventListener("scroll", function () {
        var st = document.documentElement.scrollTop;
        if (st > lastScrollTop) {
            body.addClass('scrolldown');
            body.removeClass('scrollup');
        } else if (st <= lastScrollTop) {
            body.addClass('scrollup');
            body.removeClass('scrolldown');
        }
        lastScrollTop = document.documentElement.scrollTop;
    }, false);
}
window.scrolldirection = scrolldirection;

// search open close
function openSearch() {
    $('.adminuiux-search-full').addClass('active')
}
window.openSearch = openSearch;

function closeSearch() {
    $('.adminuiux-search-full').removeClass('active');
}
window.closeSearch = closeSearch;

function contentClick() {
    if ($('.adminuiux-search-full').hasClass('active') === true) {
        $('.adminuiux-search-full').removeClass('active');
    }
    if ($('body').hasClass('sidebar-open') === true) {
        $('body').removeClass('sidebar-open');
    }
}
window.contentClick = contentClick;

//Set Active Links
function setActivelink() {
    var url = window.location.href;
    var activePage = url;
    $('#header-navbar .navbar-nav .nav-item .nav-link').each(function () {
        var linkPage = this.href;
        if (activePage == linkPage) {
            $(this).addClass("active").attr('aria-current', 'page');
        }
    });


    $(".adminuiux-sidebar .adminuiux-sidebar-inner .nav .nav-item .nav-link").each(function () {
        var linkPage = this.href;

        if (activePage == linkPage) {
            $(this).addClass("active");
            $(this).closest('.dropdown').find('.dropdown-menu').addClass('show');
            $(this).closest('.dropdown').find('.dropdown-toggle').addClass('show');
        }
    });
    $(".adminuiux-mobile-footer .nav .nav-item .nav-link").each(function () {
        var linkPage = this.href;
        if (activePage == linkPage) {
            $(this).addClass("active").attr('aria-current', 'page');
        }
    })
}
window.setActivelink = setActivelink;

//Sidebar
function initSidebar() {
    //Open/Close sidebar    
    if (windowswidth >= 992) {
        body.toggleClass('sidebar-close');
    } else {
        body.toggleClass('sidebar-open');
    }
}
window.initSidebar = initSidebar;

// image cover ion background set
function coverimg() {
    $('.coverimg').each(function () {
        $(this).css('background-image', 'url(' + $(this).find('img').attr('src') + ')');
        $(this).find('img').hide()
    })
}
window.coverimg = coverimg;

// drop down menu click dont close 
function dontclosedd() {
    $('.dropdown-dontclose').on('click blur', function (event) {
        $('.dropdown-item').removeClass('show').next('.dropdown-menu').removeClass('show');
        event.stopPropagation();
        $(this).find('.dropdown-item').addClass('show').next().addClass('show');
    });
}
window.dontclosedd = dontclosedd;

// copy code 
$('.copycode').on('click', function () {
    var thisEl = $(this);
    var text = thisEl.addClass('active').prev().find('code').text();
    var elem = document.createElement("textarea");
    document.body.appendChild(elem);
    elem.value = text;
    elem.select();
    document.execCommand('copy');
    document.body.removeChild(elem);
    setTimeout(function () {
        thisEl.removeClass('active')
    }, 500)
});

//Scroll to top
function scrollToTop() {
    document.body.scrollTop = document.documentElement.scrollTop = 0;
}
window.scrollToTop = scrollToTop;

/* auto select mode */
function autoThemeMode() {
    const runColorMode = (fn) => {
        if (!window.matchMedia) {
            return;
        }
        const query = window.matchMedia('(prefers-color-scheme: dark)');
        fn(query.matches);
        query.addEventListener('change', (event) => fn(event.matches));
    }
    runColorMode((isDarkMode) => {
        if (isDarkMode) {
            document.documentElement.setAttribute("data-bs-theme", "dark");
        } else {
            document.documentElement.setAttribute("data-bs-theme", "light");
        }
    })
}
window.autoThemeMode = autoThemeMode;

//Go back in history
function goBack() {
    window.history.go(-1);
}
window.goBack = goBack;

//Back to top
function initBackToTop() {
    var pxShow = 300;
    var scrollSpeed = 1000;
    $(window).on('scroll', function () {
        if ($(window).scrollTop() >= pxShow) {
            $("#backtotop").removeClass('d-none');
        } else {
            $("#backtotop").addClass('d-none');
        }
    });

    $('#backtotop').on('click', function () {
        document.body.scrollTop = document.documentElement.scrollTop = 0;
    });
}
window.initBackToTop = initBackToTop;

//Customize Datatable
function customizeDatatable() {
}
window.customizeDatatable = customizeDatatable;

// feather icons 
function featherjs() {
    feather.replace();
}
window.featherjs = featherjs;

// bootstrap tooltips 
function bstooltip() {
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))
}
window.bstooltip = bstooltip;

// swiper auto play no nav
function swipernav() {
    if ($('.swipernav').length > 0) {
        const swiper = new Swiper('.swipernav', {
            slidesPerView: "auto",
            spaceBetween: 16,
            autoplay: {
                delay: 2500,
                disableOnInteraction: true,
            },

        });
    }
}
window.swipernav = swipernav;

// swiper auto play nav
function swipernavpagination() {
    if ($('.swipernavpagination').length > 0) {
        const swiper2 = new Swiper('.swipernavpagination', {
            slidesPerView: "auto",
            spaceBetween: 16,
            autoplay: {
                delay: 2500,
                disableOnInteraction: true,
            },
            pagination: {
                el: '.swiper-pagination',
                type: 'bullets',
            },
        });
    }
}
window.swipernavpagination = swipernavpagination;

// dropzone 
function mydropzone() {
    if ($('.dropzone').length > 0) {
        window.Dropzone;
    }
}
window.mydropzone = mydropzone;

// editor  FroalaEditor
function froalaeditor() {
    if ($('.FroalaEditor').length > 0) {
        var editor = new FroalaEditor('.FroalaEditor');
    }
}
window.froalaeditor = froalaeditor;

/* date picker calendar */
function datepicker() {
    if ($('#datepicker').length > 0) {

        $('#datepicker').daterangepicker({
            "singleDatePicker": true,
            "minYear": 2023,
            "autoApply": true,
            "linkedCalendars": false,
            "alwaysShowCalendars": true,
            "startDate": "19/03/2024",
            "endDate": "25/03/2024",
            "opens": "center",
            "buttonClasses": "btn",
            "drops": "up",
            "locale": {
                "format": 'DD/MM/YYYY'
            },
            "applyButtonClasses": "btn-theme",
            "cancelClass": "btn-light"
        }, function (start, end, label) {
            //console.log('New date range selected: ' + start.format('YYYY-MM-DD') + ' to ' + end.format('YYYY-MM-DD') + ' (predefined range: ' + label + ')');
        });

    }
}
window.datepicker = datepicker;

/* inline calendar */
function inlinedatepicker() {
    if ($('#inlinewrap1').length > 0) {

        $('#inlinewrap1').daterangepicker({
            "singleDatePicker": true,
            "minYear": 2023,
            "autoApply": true,
            "linkedCalendars": false,
            "alwaysShowCalendars": true,
            "parentEl": ".inlinewrap1",
            "startDate": "19/03/2024",
            "endDate": "25/03/2024",
            "opens": "center",
            "buttonClasses": "btn",
            "drops": "up",
            "locale": {
                "format": 'DD/MM/YYYY'
            },
            "applyButtonClasses": "btn-theme",
            "cancelClass": "btn-light"
        }, function (start, end, label) {
            //console.log('New date range selected: ' + start.format('YYYY-MM-DD') + ' to ' + end.format('YYYY-MM-DD') + ' (predefined range: ' + label + ')');
        });

        /* inline calendar activate  */
        $('#inlinewrap1').click();

    }
}
window.inlinedatepicker = inlinedatepicker;

// date range picker 
function daterange() {
    if ($('#daterangepicker').length > 0) {
        $('#daterangepicker').daterangepicker({
            "minYear": 2023,
            "autoApply": true,
            "linkedCalendars": false,
            "alwaysShowCalendars": true,
            "startDate": "19/03/2024",
            "endDate": "25/03/2024",
            "opens": "center",
            "buttonClasses": "btn",
            "drops": "down",
            "locale": {
                "format": 'DD/MM/YYYY'
            },
            "applyButtonClasses": "btn-theme",
            "cancelClass": "btn-light"
        }, function (start, end, label) {
            //console.log('New date range selected: ' + start.format('YYYY-MM-DD') + ' to ' + end.format('YYYY-MM-DD') + ' (predefined range: ' + label + ')');
        });
    }
}
window.daterange = daterange;

// date range picker with predefined range
function daterangeranges() {
    if ($('#daterangepickerranges').length > 0) {
        $('#daterangepickerranges').daterangepicker({
            "minYear": 2023,
            "autoApply": false,
            "linkedCalendars": false,
            "alwaysShowCalendars": true,
            "startDate": "19/03/2024",
            "endDate": "25/03/2024",
            "opens": "center",
            "buttonClasses": "btn",
            "drops": "down",
            "locale": {
                "format": 'DD/MM/YYYY'
            },
            "applyButtonClasses": "btn-theme",
            "cancelClass": "btn-light",
            "ranges": {
                'Today': [moment(), moment()],
                'Yesterday': [moment().subtract(1, 'days'), moment().subtract(1, 'days')],
                'Last 7 Days': [moment().subtract(6, 'days'), moment()],
                'Last 30 Days': [moment().subtract(29, 'days'), moment()],
                'This Month': [moment().startOf('month'), moment().endOf('month')],
                'Last Month': [moment().subtract(1, 'month').startOf('month'), moment().subtract(1, 'month').endOf('month')]
            },
        }, function (start, end, label) {
            //console.log('New date range selected: ' + start.format('YYYY-MM-DD') + ' to ' + end.format('YYYY-MM-DD') + ' (predefined range: ' + label + ')');
        });
    }
}
window.daterangeranges = daterangeranges;

//dataTable global
function dataTables() {
    /* Initialize dataTable */
    if ($('#dataTable').length > 0) {
        $('#dataTable').DataTable({
            searching: false,
            lengthChange: false,
            autoWidth: false,
            columnDefs: [{ orderable: false, targets: 4 }],
            order: [[0, 'desc']],
            pageLength: 6,
            responsive: true,
        });
        $('#dataTable tr').find('td:visible:last').addClass('lastvisible');
    }

}
window.dataTables = dataTables;

function adjustDataTable() {
    /* resize */
    var table = $('#dataTable').DataTable();
    table.columns.adjust().draw();
    lastvisibletd();
}
window.adjustDataTable = adjustDataTable;

/* responsive last visible table cell after cell hides*/
function lastvisibletd() {
    $('.table tbody tr td').removeClass('lastvisible');
    $('.table tbody tr').each(function () {
        var thisis = $(this);
        thisis.find('td:visible:last').addClass('lastvisible');
    })
}
window.lastvisibletd = lastvisibletd;

/* pasword strength checker */
function checkStrength(password, fieldpasswrap) {
    var strength = 0;

    if (password.length < 6 || password.length < 1) {
        $('#checksterngthdisplay').removeClass().addClass('short check-strength');
        $('#textpassword').removeClass().addClass('text-secondary small');
        return 'Too short'
    }
    if (password.length > 7) strength += 1
    // If password contains both lower and uppercase characters, increase strength value.  
    if (password.match(/([a-z].*[A-Z])|([A-Z].*[a-z])/)) strength += 1
    // If it has numbers and characters, increase strength value.  
    if (password.match(/([a-zA-Z])/) && password.match(/([0-9])/)) strength += 1
    // If it has one special character, increase strength value.  
    if (password.match(/([!,%,&,@,#,$,^,*,?,_,~])/)) strength += 1
    // If it has two special characters, increase strength value.  
    if (password.match(/(.*[!,%,&,@,#,$,^,*,?,_,~].*[!,%,&,@,#,$,^,*,?,_,~])/)) strength += 1
    // Calculated strength value, we can return messages  
    // If value is less than 2  
    if (strength < 2) {
        $('#checksterngthdisplay').removeClass().addClass('weak check-strength');
        $('#textpassword').removeClass().addClass('text-danger small');
        fieldpasswrap.removeClass('is-valid');
        return 'This is a weak';
    } else if (strength == 2) {
        $('#checksterngthdisplay').removeClass().addClass('good check-strength');
        $('#textpassword').removeClass().addClass('text-warning small');
        fieldpasswrap.removeClass('is-valid');
        return 'This is a good';
    } else {
        $('#checksterngthdisplay').removeClass().addClass('strong check-strength');
        $('#textpassword').removeClass().addClass('text-success small');
        fieldpasswrap.addClass('is-valid');
        return 'Wow! Its a strong';
    }
}
window.checkStrength = checkStrength;

/* passsword strength checker */
function checkstrength() {
    if ($('#checkstrength').length > 0) {
        $('#checkstrength').on('keyup', function () {

            var fieldpass = $(this);
            var fieldpasswrap = $(this).closest('.check-valid');
            checkStrength(fieldpass.val(), fieldpasswrap);

            if (this.value != '') {
                $('#textpassword').html(checkStrength(fieldpass.val(), fieldpasswrap))
                fieldpass.closest('.check-valid').next('.invalid-feedback').hide();
                // $(this).closest('.check-valid').addClass('is-valid');
            } else {
                fieldpasswrap.removeClass('is-valid').next('.invalid-feedback').show().text("Please enter valid input")
                $('#checksterngthdisplay').removeClass();
            }
        });
    }
}
window.checkstrength = checkstrength;

/* inner sidebar close */
function innersidebar() {
    $('body').toggleClass('innermenu-close');
}
window.innersidebar = innersidebar;

/* header h padding top*/
function headerpaddingTop() {
    if ($('.header-pt').length > 0) {
        $('.header-pt').css('top', $('header.adminuiux-header > .navbar').outerHeight())
    }
}
window.headerpaddingTop = headerpaddingTop;

/* bootstrap popover  */
function bspopover() {
    const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]')
    const popoverList = [...popoverTriggerList].map(popoverTriggerEl => new bootstrap.Popover(popoverTriggerEl))
}
window.bspopover = bspopover;

/* bootstrap toast message */
function bstoast() {
    const toastElList = document.querySelectorAll('.toast')
    const toastList = [...toastElList].map(toastEl => new bootstrap.Toast(toastEl))
}
window.bstoast = bstoast;

/* Range Customize */
function range2() {
    const rangeEle = document.querySelector("#range2")
    const rangeValue = document.querySelector(".value2")

    rangeEle.addEventListener("input", (event) => {
        const temprangeValue = event.target.value;
        rangeValue.textContent = temprangeValue;

        const progress = (temprangeValue / rangeEle.max) * 100;

        rangeEle.style.background = `linear-gradient(to right, var(--adminuiux-theme-1) ${progress}%, var(--adminuiux-bg-1) ${progress}%)`;
    })
}
window.range2 = range2;

// 2
function range3() {
    const rangeEle3 = document.querySelector("#range3")
    const rangeValue3 = document.querySelector(".value3")

    rangeEle3.addEventListener("input", (event) => {
        const temprangeValue = Number(event.target.value);

        rangeValue3.textContent = temprangeValue;

        const progress = (temprangeValue / rangeEle3.max) * 100;

        rangeEle3.style.background = `linear-gradient(to right, var(--adminuiux-theme-1) ${progress}%, var(--adminuiux-bg-1) ${progress}%)`;

        rangeEle3.style.setProperty("--thumb-rotate", `${(temprangeValue / 100) * 2160}deg`)
    })
}
window.range3 = range3;

// 2
function range4() {
    const rangeEle4 = document.querySelector("#range4")
    const rangeValue4 = document.querySelector(".value4")

    rangeEle4.addEventListener("input", (event) => {
        const temprangeValue = event.target.value;
        rangeValue4.textContent = temprangeValue;

        const progress = (temprangeValue / rangeEle4.max) * 100;

        rangeEle4.style.background = `linear-gradient(to right, var(--adminuiux-theme-1) ${progress}%, var(--adminuiux-bg-1) ${progress}%)`;
    })
}
window.range4 = range4;

if ($('.rangevalue').length > 0) {
    $('.rangevalue').each(function () {
        var ranges = $(this);
        $('#' + ranges.attr('data-value')).val(ranges.val());
        ranges.on('mousemove', function () {
            $('#' + ranges.attr('data-value')).val(ranges.val());
        })
    })
}
if ($('.rangevalues').length > 0) {
    $('.rangevalues').each(function () {
        var rangesval = $(this);
        var setrangeval = rangesval.attr('id');

        rangesval.on('change', function () {
            $('[data-value="' + setrangeval + '"]').val(rangesval.val())
        })
    })
}

function selectable() {
    if ($('.selectable').length > 0) {
        $('.selectable').on('click', function () {
            if ($(this).hasClass('anyone') === true) {
                $('.selectable').removeClass('active');
                $(this).addClass('active');
            } else {
                $(this).toggleClass('active');
            }
        })
    }
}
window.selectable = selectable;

function isinframe() {
    if (self !== top) {
        body.addClass('adminuiux-in-iframe')
    } else {
        body.removeClass('adminuiux-in-iframe')
    }
}
window.isinframe = isinframe;

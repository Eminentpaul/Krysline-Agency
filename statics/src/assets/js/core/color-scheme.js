'use strict'
var html = $('html');
var body = $('body');

$(document).ready(function () {

    $('#btn-layout-modes-dark').on('click', function () {
        if ($(this).is(':checked')) {
            setCookie('adminuiuxlayoutmode', 'dark-mode', 1);
            html.attr('class', getCookie("adminuiuxlayoutmode"));
        } else {
            setCookie('adminuiuxlayoutmode', 'light-mode', 1);
            html.attr('class', getCookie("adminuiuxlayoutmode"));
        }
    });

    /* color style  */
    var curentstyle = body.attr('data-theme');
    if ($.type(getCookie("adminuiuxtheme")) != 'undefined' && getCookie("adminuiuxtheme") != '') {

        body.addClass(getCookie("adminuiuxtheme"));
        body.attr('data-theme', getCookie("adminuiuxtheme"));
        curentstyle = getCookie("adminuiuxtheme");

        $('.theme-select .select-box').each(function () {
            if ($(this).attr('data-title') === getCookie("adminuiuxtheme")) {
                $(this).addClass("active");
            }
        });
    }
    $('.theme-select').find('.select-box').each(function () {
        $(this).on('click', function () {
            $('.theme-select').find('.select-box').removeClass('active');

            if ($(this).hasClass('active') != true && setstyle != '') {
                var curentstyle = body.attr('data-theme');
                var setstyle = $(this).attr('data-title');

                $(this).addClass('active');
                body.removeClass(curentstyle).addClass(setstyle).attr('data-theme', setstyle);
                setCookie('adminuiuxtheme', setstyle, 1);
                curentstyle = setstyle;
            }
        });
    });

    /* background images */
    if ($.type(getCookie("adminuiuxsetimagepath")) != 'undefined' && getCookie("adminuiuxsetimagepath") != '') {
        $('.main-bg').each(function () {
            $(this).css('--adminuiux-main-bg', 'url("../../' + getCookie("adminuiuxsetimagepath") + '")');
        });

        $('.theme-background .select-box').each(function () {
            if ($(this).attr('data-src') === getCookie("adminuiuxsetimagepath")) {
                $(this).addClass("active");
            }
        });
    }
    $('.theme-background .select-box').on('click', function () {
        $('.theme-background .select-box').removeClass('active');
        $('.main-bg').removeClass(getCookie("adminuiuxsetimagepath"));
        var mainbgimage = $(this).find('img').attr('src');

        $(this).addClass("active");
        if (mainbgimage !== undefined) {
            setCookie('adminuiuxsetimagepath', mainbgimage, 1);
            $('.main-bg').each(function () {
                $(this).css('--adminuiux-main-bg', 'url(../../' + mainbgimage + ')');
            });
        } else {
            $('.main-bg').each(function () {
                setCookie('adminuiuxsetimagepath', '', 1);
                $(this).css('--adminuiux-main-bg', 'none');
            });
        }
    });

    /* sidebar color fill type */
    var curentSidebarFill = body.attr('data-sidebarfill');
    if ($.type(getCookie("adminuiuxsidebarfilled")) != 'undefined' && getCookie("adminuiuxsidebarfilled") != '') {

        body.removeClass(curentSidebarFill).addClass(getCookie("adminuiuxsidebarfilled")).attr('data-sidebarfill', getCookie("adminuiuxsidebarfilled"));
        curentSidebarFill = getCookie("adminuiuxsidebarfilled");

        $('#personalise-preview-sidebar .select-box').each(function () {
            $(this).removeClass("active");
            if ($(this).attr('data-title') === getCookie("adminuiuxsidebarfilled")) {
                $(this).addClass("active");
            }
        });
    }
    $('#personalise-preview-sidebar .select-box').on('click', function () {
        var setSidebarfill = $(this).attr('data-title');
        body.removeClass(curentSidebarFill);

        $('#personalise-preview-sidebar .select-box').removeClass('active');
        $(this).addClass("active");

        if (setSidebarfill != "") {
            body.removeClass(getCookie("adminuiuxsidebarfilled")).addClass(setSidebarfill);
            setCookie('adminuiuxsidebarfilled', setSidebarfill, 1);
        } else {
            body.removeClass(getCookie("adminuiuxsidebarfilled"));
            removeCookie('adminuiuxsidebarfilled');
        }
    });

    /* sidebar layout */
    var currentsidebarlayout = body.attr('data-sidebarlayout');
    if ($.type(getCookie("adminuiuxsidebarlayout")) != 'undefined' && getCookie("adminuiuxsidebarlayout") != '') {
        body.removeClass(currentsidebarlayout).addClass(getCookie("adminuiuxsidebarlayout")).attr('data-sidebarlayout', getCookie("adminuiuxsidebarlayout"));

        $('.sidebar-layout .select-box').each(function () {
            $(this).removeClass("active");
            if ($(this).attr('data-title') === getCookie("adminuiuxsidebarlayout")) {
                $(this).addClass("active");
            }
        });
    }
    $('.sidebar-layout .select-box').on('click', function () {
        var setSidebarlayout = $(this).attr('data-title');
        var currentsidebarlayout = body.attr('data-sidebarlayout');
        body.removeClass(currentsidebarlayout).attr('data-sidebarlayout', setSidebarlayout);

        $('.sidebar-layout .select-box').removeClass('active');
        $(this).addClass("active");

        if (setSidebarlayout != "") {
            body.removeClass(getCookie("adminuiuxsidebarlayout")).addClass(setSidebarlayout);
            setCookie('adminuiuxsidebarlayout', setSidebarlayout, 1);
        } else {
            body.removeClass(getCookie("adminuiuxsidebarlayout"));
            removeCookie('adminuiuxsidebarlayout');
        }
    });

    /* header style */
    if ($.type(getCookie("adminuiuxheaderfilled")) != 'undefined' && getCookie("adminuiuxheaderfilled") != '') {
        body.addClass(getCookie("adminuiuxheaderfilled"));

        $('#personalise-preview-header .select-box').each(function () {
            $(this).removeClass("active");
            if ($(this).attr('data-title') === getCookie("adminuiuxheaderfilled")) {
                $(this).addClass("active");
            }
        });
    }
    $('#personalise-preview-header .select-box').on('click', function () {
        var setheaderfill = $(this).attr('data-title');

        $('#personalise-preview-header .select-box').removeClass('active');
        $(this).addClass("active");

        if (setheaderfill != "") {
            body.removeClass(getCookie("adminuiuxheaderfilled")).addClass(setheaderfill);
            setCookie('adminuiuxheaderfilled', setheaderfill, 1);
        } else {
            body.removeClass(getCookie("adminuiuxheaderfilled"));
            removeCookie('adminuiuxheaderfilled');
        }
    });

    /* header layout */
    var currentheaderlayout = body.attr('data-headerlayout');
    if ($.type(getCookie("adminuiuxheaderlayout")) != 'undefined' && getCookie("adminuiuxheaderlayout") != '') {
        body.removeClass(currentheaderlayout).addClass(getCookie("adminuiuxheaderlayout")).attr('data-headerlayout', getCookie("adminuiuxheaderlayout"));

        $('#header-layout .select-box').each(function () {
            $(this).removeClass("active");
            if ($(this).attr('data-title') === getCookie("adminuiuxheaderlayout")) {
                $(this).addClass("active");
            }
        });
    }
    $('#header-layout .select-box').on('click', function () {
        var setheaderlayout = $(this).attr('data-title');
        var currentheaderlayout = body.attr('data-headerlayout');
        body.removeClass(currentheaderlayout).attr('data-headerlayout', setheaderlayout);

        $('#header-layout .select-box').removeClass('active');
        $(this).addClass("active");

        if (setheaderlayout != "") {
            body.removeClass(getCookie("adminuiuxheaderlayout")).addClass(setheaderlayout);
            setCookie('adminuiuxheaderlayout', setheaderlayout, 1);
        } else {
            body.removeClass(getCookie("adminuiuxheaderlayout"));
            removeCookie('adminuiuxheaderlayout');
        }
    });

    /* bg gradient */
    var currentbggradient = body.attr('data-bggradient');
    if ($.type(getCookie("adminuiuxbggradient")) != 'undefined' && getCookie("adminuiuxbggradient") != '') {
        body.removeClass(currentbggradient).addClass(getCookie("adminuiuxbggradient")).attr('data-bggradient', getCookie("adminuiuxbggradient"));

        $('.theme-background .gradient-box').each(function () {
            $(this).removeClass("active");
            if ($(this).attr('data-title') === getCookie("adminuiuxbggradient")) {
                $(this).addClass("active");
            }
        });
    }
    $('.theme-background .gradient-box').on('click', function () {
        var setbggradient = $(this).attr('data-title');
        var currentbggradient = body.attr('data-bggradient');
        body.removeClass(currentbggradient).attr('data-bggradient', setbggradient);

        $('.theme-background .gradient-box').removeClass('active');
        $(this).addClass("active");

        if (setbggradient != "") {
            body.removeClass(getCookie("adminuiuxbggradient")).addClass(setbggradient);
            setCookie('adminuiuxbggradient', setbggradient, 1);
        } else {
            body.removeClass(getCookie("adminuiuxbggradient"));
            removeCookie('adminuiuxbggradient');
        }
    });


    //dark mode
    initDarkMode();

    // RTL 
    initRTL();

    // auto theme mode
    //autoThemeMode();

    /* Right to left to right directions  */
    if (getCookie('adminuiuxdirectionmode') === 'rtl') {
        $('#btn-layout-RTL').prop('checked', true);
        html.addClass('rtl');
        html.attr('dir', 'ltr');

    } else {
        $('#btn-layout-RTL').prop('checked', false);
        html.attr('dir', '');
        html.removeClass('rtl');
    }
    $('#btn-layout-RTL').on('click', function () {
        if ($(this).is(':checked')) {
            setCookie('adminuiuxdirectionmode', 'rtl', 1);
            html.attr('dir', 'rtl');
            html.addClass('rtl');

        } else {
            setCookie('adminuiuxdirectionmode', 'ltr', 1);
            html.attr('dir', '');
            html.removeClass('rtl');
        }
    });

});


/* create cookie */
function setCookie(cname, cvalue, exdays) {
    const d = new Date();
    d.setTime(d.getTime() + (exdays * 24 * 60 * 60 * 1000));
    let expires = "expires=" + d.toUTCString();
    document.cookie = cname + "=" + cvalue + ";" + expires + ";  path=/; SameSite=None; Secure";
}

function getCookie(cname) {
    let name = cname + "=";
    let ca = document.cookie.split(';');
    for (let i = 0; i < ca.length; i++) {
        let c = ca[i];
        while (c.charAt(0) == ' ') {
            c = c.substring(1);
        }
        if (c.indexOf(name) == 0) {
            return c.substring(name.length, c.length);
        }
    }
    return "";
}

//Dark Mode
function initDarkMode() {
    /* layout modes dark-light */
    if (getCookie("adminuiuxlayoutmode") === 'dark') {
        $('#btn-layout-modes-dark').prop('checked', true);
        document.documentElement.setAttribute("data-bs-theme", "dark");
        $('#btn-layout-modes-dark-page').addClass('active')
    } else {
        $('#btn-layout-modes-dark').prop('checked', false);
        document.documentElement.setAttribute("data-bs-theme", "light");
        $('#btn-layout-modes-dark-page').removeClass('active');
    }
    if ($('#btn-layout-modes-dark').length > 0) {
        $('#btn-layout-modes-dark').on('change', function () {
            if ($(this).prop('checked') === true) {
                document.documentElement.setAttribute("data-bs-theme", "dark");
                setCookie("adminuiuxlayoutmode", 'dark', 1);
                $('#btn-layout-modes-dark-page').addClass('active');
            } else {
                document.documentElement.setAttribute("data-bs-theme", "light");
                setCookie("adminuiuxlayoutmode", 'light', 1);
                $('#btn-layout-modes-dark-page').removeClass('active');
            }
        });
    }
    if ($('#btn-layout-modes-dark-page').length > 0) {
        $('#btn-layout-modes-dark-page').on('click', function () {
            if ($(this).hasClass('active') === true) {
                document.documentElement.setAttribute("data-bs-theme", "light");
                setCookie("adminuiuxlayoutmode", 'light', 1);
                $(this).removeClass('active')
                $('#btn-layout-modes-dark').prop('checked', false);
            } else {
                document.documentElement.setAttribute("data-bs-theme", "dark");
                setCookie("adminuiuxlayoutmode", 'dark', 1);
                $(this).addClass('active');
                $('#btn-layout-modes-dark').prop('checked', true);
            }
        });
    }
}

//rtl
function initRTL() {
    $('#btn-layout-dir-rtl').on('change', function () {
        if ($(this).prop('checked') === true) {
            document.documentElement.setAttribute("dir", "rtl");
        } else {
            document.documentElement.setAttribute("dir", "ltr");
        }
    });

    $('#btn-layout-dir-rtl-page').on('change', function () {
        if ($(this).prop('checked') === true) {
            document.documentElement.setAttribute("dir", "rtl");
        } else {
            document.documentElement.setAttribute("dir", "ltr");
        }
    });
}
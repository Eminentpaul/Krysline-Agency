/*! main.js | Adminuiux 2023-2024 */

/* ==========================================================================
Main initialization file
========================================================================== */

"use strict";

import $ from 'jquery';
window.jQuery = $;
window.$ = $;

$(window).on('load', function () {

    // main links active 
    setActivelink();

    // set header space 
    fixedHeaderSpace()

    // fixed sticky footer space
    fixedFooterSpace()

    //feature icons 
    featherjs();

    // cover img background set
    coverimg();

    // don't close dropdown
    dontclosedd()

    // bs tooltip 
    bstooltip();

    // swiper common 
    swipernav();
    swipernavpagination();

    // dropzone 
    mydropzone();

    // froala editor 
    froalaeditor();

    //datepicker class
    datepicker();

    // global date range 
    daterange();

    // date range with ranges
    daterangeranges();

    //dataTable global
    dataTables();

    //inline datepicker
    inlinedatepicker();

    /* bootstrap popover  */
    bspopover();

    /* bootstrap toast message */
    bstoast();

    /* bootstrap tooltips */
    bstooltip();

    /* header padding top */
    headerpaddingTop();

    /* selectable active toggle */
    selectable();

    /* back to top */
    initBackToTop();

    // hide page loader 
    PageLoaderHide()

    // in iframe 
    isinframe();
});

$(window).on('scroll', function () {
    // active header
    activeHeader();

    scrolldirection();
})

$(window).on('resize', function () {
    // active header
    adjustDataTable()
})

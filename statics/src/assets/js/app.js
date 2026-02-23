import "../scss/style.scss";

//jQuery 
import $ from 'jquery';
window.jQuery = $;
window.$ = $;

// Popper js
import { createPopper } from '@popperjs/core';

// Bootstrap 
import * as bootstrap from "bootstrap";
// Note: If you want to make bootstrap globally available, e.g. for using `bootstrap.modal`
window.bootstrap = bootstrap;

// Feather icons
import feather from "feather-icons";
window.feather = feather;

// Chart js
import Chart from "chart.js/auto";
window.Chart = Chart;

// Siwper bundle 
import Swiper from 'swiper';
window.Swiper = Swiper;

// Moments js
import moment from 'moment';
window.moment = moment

// Daterangepicker 
import daterangepicker from 'bootstrap-daterangepicker';
window.daterangepicker = daterangepicker;

// DataTable
import 'datatables.net'
window.dataTables = dataTables;

// DataTable Responsive
import 'datatables.net-responsive'

// Dragula
import dragula from 'dragula';
window.dragula = dragula;

// Dropzone
import Dropzone from "dropzone";
window.Dropzone = Dropzone;

// FullCalendar
import { Calendar } from '@fullcalendar/core';
import dayGridPlugin from '@fullcalendar/daygrid';
import timeGridPlugin from '@fullcalendar/timegrid';
import listPlugin from '@fullcalendar/list';
window.Calendar = Calendar;
window.dayGridPlugin = dayGridPlugin;
window.timeGridPlugin = timeGridPlugin;
window.listPlugin = listPlugin;

// Froala Editor
import FroalaEditor from 'froala-editor'
window.FroalaEditor = FroalaEditor;

// Progressbar min js
import ProgressBar from "progressbar.js"
window.ProgressBar = ProgressBar;

// SmartWizard
import smartWizard from 'smartwizard';
window.smartWizard = smartWizard;

// Lozad
import lozad from 'lozad';
window.lozad = lozad;

// Simplebar
import 'simplebar';


// global js
import './core/functions.js';
import './core/main.js';
import './core/responsive.js';
import './core/color-scheme.js'


; (function ($, win, doc, undefined) {

	'use strict';
	
	$plugins.common = {
		init: function (opt) {
			
			$plugins.uiInputClear();
			$plugins.uiCaption();

			(!$plugins.browser.mobile) ? $plugins.uiSelect() : '';

			$(win).on('scroll', function () {
				scrollChange($(win).scrollTop());
			});

			$plugins.uiHasScrollBar({ selector:$('body') }) ? $('html').addClass('is-scroll') : $('html').removeClass('is-scroll');

			function scrollChange(v) {
				var win_h = $(win).outerHeight();
				v > 0
					? $('body').addClass('scrolled')
					: $('body').removeClass('scrolled');

				v + win_h + 10 > $(doc).outerHeight()
					? $('body').addClass('scrolled-b')
					: $('body').removeClass('scrolled-b');

				v > win_h / 2
					? $('body').addClass('scroll-top')
					: $('body').removeClass('scroll-top');
			}

			scrollChange($(win).scrollTop());

			/* 2019-12-13 JH�섏젙 */
			/*
			$plugins.uiAjax({ 
                id:'baseHeader', 
                url:'../../html/inc/header.html',
                page:true,
				callback:function(){
                    $plugins.common.header(opt);
                }
            });

			$plugins.uiAjax({ 
                id:'baseFooter', 
                url:'../../html/inc/footer.html',
                page:true,
				callback:function(){
                    $plugins.common.footer(opt);
                }
            });
			
			//html�덉떆��
			$('.search-wrap input.inp-base, .base-search-wrap input.inp-base, .main-sec1-search .search-wrap input').on('focus', function(){
				$plugins.common.searchShow();
			})
			$('.search-wrap input.inp-base, .base-search-wrap input.inp-base, .main-sec1-search .search-wrap input').on('blur', function(){
				$plugins.common.searchHide();
			})
			*/
			$plugins.common.uiToggleBtn();
			
			$plugins.common.header({id: 'baseHeader'});
			$plugins.common.footer({id: 'baseFooter'});


		},
		uiToggleBtn: function(){
			$('.ui-togglebtn button').off('click.tg').on('click.tg', function(){
				$(this).closest('.ui-togglebtn').find('button').removeClass('btn-base-imp').addClass('btn-base');
				$(this).removeClass('btn-base').addClass('btn-base-imp')
			});
			// OpenAPI Sample Code(modify-202204)
			$plugins.uiTab({
				id: 'sample-code'
			});
		},
		header: function (opt) {
			var $nav = $('#baseNav'),
				$li_1 = $nav.find('.nav-main-1'),
				$btn_1 = $nav.find('.nav-btn-1'),
				timer;
			
			$('.ui-menu').on('click', function(){
				$('.header-mobile').addClass('on');
			});
			$('.menu-wrap .btn-close').on('click', function(){
				$('.header-mobile').removeClass('on');
			});

	

			$btn_1.on('mouseover focus', function(){
				clearTimeout(timer);
				$plugins.common.navShow(this);
			}).on('mouseleave blur', function(){
			//	hideTimer();
			});

			$('.nav-sub').on('mouseover focus', function(){
				clearTimeout(timer);
			}).on('mouseleave', function(){
				hideTimer();
			});
			$(".base-header").on('mouseleave', function(){
				hideTimer();
			});
			
			//20200826 ��씠�숈떆 硫붾돱 �덉씠�� �덈뱺�섎룄濡� �섍린�꾪븿... 
			$(".header-lnb").on('mouseover focusin', function() {
				hideTimer();
			});
			
			function hideTimer() {
				timer = setTimeout(function(){
					$plugins.common.navHide();
				},200);
			}

			$plugins.uiAccordion({ 
				id:'menu0205', 
				current:null, 
				autoclose:false
			});
			$plugins.uiAccordion({ 
				id:'menu0206', 
				current:null, 
				autoclose:false
			});
			$plugins.uiAccordion({ 
				id:'submenu0205', 
				current:null, 
				autoclose:false
			});
			$plugins.uiAccordion({ 
				id:'submenu0206', 
				current:null, 
				autoclose:false
			});
			function selectedRemove(){
				$('.menu-wrap-body .dep-1').removeClass('selected');
			}
			selectedRemove();
			$('.dep-1').eq(0).addClass('selected');

			//menu event
			$('.dep-1-btn').on('click', function(){
				selectedRemove();
				$(this).closest('.dep-1').addClass('selected');
			});

			$plugins.uiDropdown({ 
				id:'uiMeunSub', 
				ps:'bl', 
				eff:'st', 
				auto: false,
				dim:true,
				openback: function() { console.log('open callback'); },
				closeback: function() { console.log('close callback'); },
				offset:false 
			});
		},
		menuOpen: function () {
			var $uiMenu = $('#uiMenu');
			$uiMenu.removeClass('nomotion');
			$uiMenu.off('transitionend.uimenu');

			$uiMenu.find('.dep-1-wrap').css({
				'height': $(win).outerHeight() - $uiMenu.find('.menu-wrap-head').outerHeight(),
				'overflow-y':'auto'
			});
			$uiMenu.find('.dep-2-wrap').css({
				'height': $(win).outerHeight() - $uiMenu.find('.menu-wrap-head').outerHeight(),
				'overflow-y':'auto'
			});

			// $('body').data('sct', $(win).scrollTop()).css({
			// 	position: 'fixed',
			// 	marginTop: $(win).scrollTop() * -1
			// });
			$('body').addClass('menu-on');
			$uiMenu.find('button, a, label, input').eq(0).focus();
			
			//setTimeout(function () {
				$uiMenu.addClass('on');
				$('.menu-dim').addClass('on');
			//}, 10);
		},
		menuClose: function (opt) {
			var $uiMenu = $('#uiMenu');

			if (opt !== undefined && opt.nomotion !== undefined) {
				$uiMenu.addClass('nomotion');
				$uiMenu.removeClass('on');
				motionend();
			} else {
				$uiMenu.removeClass('on');
			}

			$uiMenu.off('transitionend.uimenu').on('transitionend.uimenu', function () {
				motionend();
			});
			function motionend(){

				$('body').removeClass('menu-on');
				$('body').removeAttr('style');
				$plugins.uiScroll({
					value: $('body').data('sct'),
					speed:0
				})
				$('#baseHeader .btn-menu').focus();

				opt !== undefined && opt.callback !== undefined
					? opt.callback()
					: '';
			}
			$('.menu-dim').removeClass('on');
		},
		
		searchShow: function(){
			$('.search-frame').show();
		},
		searchHide: function(){
			$('.search-frame').hide();
		},
		navShow: function(t){
			$(t).closest('.nav-main-1').siblings('li').find('.nav-btn-1').data('selected',false);
			$(".nav-main").addClass("on")
			$(".nav-sub-wrap ul").mouseenter(function(){
				$('.nav-main-1').removeClass("on");
				$(this).parent().parent().parent().addClass("on")
			});
			if (!$(t).data('selected')) {
				$(t).data('selected', true);	
				$('.nav-main-1').removeClass('on');
				$(t).closest('.nav-main-1').addClass('on');
				
			}
			
		},
		navHide: function(){
			$('.nav-btn-1').data('selected', false);
			$(".nav-main").removeClass("on")
			$('.nav-main-1').removeClass('on');
			
			// $('.nav-main-1').removeClass('on').find('.nav-sub').stop().animate({
			// 	height: 0,
			// 	opacity:0
			// },150);
			// $('.dim-nav').removeClass('on').stop().animate({
			// 	top: 121,
			// 	height: 0
			// },200)
		},
		
       
		footer: function () {
			console.log('footer');
		}
	};
	//page
	$plugins.page = {}

	//callback
	$plugins.callback = {
		modal: function (modalId) {
			$plugins.uiInputClear();
			$plugins.uiCaption();

			setTimeout(function(){
				$plugins.uiScroll({ target:$('#' + modalId + ' .ui-modal-cont'), value:0, speed:100})
			},10)
			
		
			
			switch (modalId) {
				case 'modalTest2':

					break;
			}
		}
	}
})(jQuery, window, document);
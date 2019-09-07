/*!
 * Name:        dkrypt-util
 * Version:     1.0
 * Description: Utility javascript functions and creation of the namespace
 * Author:      Kom Sihon
 * Support:     http://d-krypt.com
 *
 * Depends:
 *      jquery.js http://jquery.org
 *
 * Date: Sat Nov 10 07:55:29 2012 -0500
 */
(function(w) {
    var c = function() {
        return new c.fn.init()
    }
    c.fn = c.prototype = {
        init: function(){return this}
    }
    
    Number.prototype.formatMoney = function(decPlaces, thouSeparator, decSeparator) {
        var n = this,
        decPlaces = isNaN(decPlaces = Math.abs(decPlaces)) ? 0 : decPlaces,
        decSeparator = decSeparator == undefined ? "," : decSeparator, thouSeparator = thouSeparator == undefined ? "." : thouSeparator,
        sign = n < 0 ? "-" : "",
        i = parseInt(n = Math.abs(+n || 0).toFixed(decPlaces)) + "",
        j = (j = i.length) > 3 ? j % 3 : 0;
        return sign + (j ? i.substr(0, j) + thouSeparator : "") + i.substr(j).replace(/(\d{3})(?=\d)/g, "$1" + thouSeparator) + (decPlaces ? decSeparator + Math.abs(n - i).toFixed(decPlaces).slice(2) : "");
    }

    c.CookieUtil = {
        get: function (name) {
            var cookieName = encodeURIComponent(name) + '=',
            cookieStart = document.cookie.indexOf(cookieName),
            cookieValue = null;
            if (cookieStart > -1) {
                var cookieEnd = document.cookie.indexOf(';', cookieStart)
                if (cookieEnd == -1){
                    cookieEnd = document.cookie.length;
                }
                cookieValue = decodeURIComponent(document.cookie.substring(cookieStart + cookieName.length, cookieEnd));
            }
            return cookieValue;
        },
        set: function (name, value, expires, path, domain, secure) {
            var cookieText = encodeURIComponent(name) + '=' +
            encodeURIComponent(value);
            if (expires instanceof Date) {
                cookieText += '; expires=' + expires.toGMTString();
            }
            if (path) {
                cookieText += '; path=' + path;
            }
            if (domain) {
                cookieText += '; domain=' + domain;
            }
            if (secure) {
                cookieText += '; secure';
            }
            document.cookie = cookieText;
        },
        unset: function (name, path, domain, secure){
            this.set(name, '', new Date(0), path, domain, secure);
        }
    }
                
    c.initPayPal = function(trigger, data, f1, f2) {
        $.getJSON('/ajaxHandlers/paypal/SetExpressCheckout.php', data, function(response) {
            if (response.error) {
                f1()
            } else {
                yamo.paypalRedirectURL = response.redirectURL
                loadPayPalScriptAndInitLightBox(trigger, f2)
            }
        })
    }         
    
    function loadPayPalScriptAndInitLightBox(trigger, fn) {
        $.getScript('https://www.paypalobjects.com/js/external/dg.js', function() {
            var dg1 = new PAYPAL.apps.DGFlow({trigger: trigger});  
            function MyEmbeddedFlow(embeddedFlow) {
                this.embeddedPPObj = embeddedFlow;
                this.paymentSuccess = function() {
                    this.embeddedPPObj.closeFlow();
                    window.location.href = 'http://' + window.location.hostname + '/ajaxHandlers/paypal/ReviewOrder.php';
                };
                this.paymentCanceled = function() {
                    this.embeddedPPObj.closeFlow();
                    window.location.href = 'unknownError.php';
                };
            }
            var ef1 = new MyEmbeddedFlow(dg1);
            if (fn) fn()
        })
    }
    /**
     * Init Fancy Combo-Boxes
     */
	$(function() {
		$('.fancy-combo-box').each(function() {
            var h = $(this).find('input[type=text]').height(),
                w = $(this).find('input[type=text]').width()
		        $(this).find('.entries-overlay').css({'padding-top': h + 5, 'width': w + 30})
        })
		$('.fancy-combo-box').click(function() {
			$(this).find('.entries-overlay').toggleClass('hidden')
		})
		$('.fancy-combo-box').on('click', '.entry', function(e) {
			var val = $(this).attr('val')
			var _$textInput = $(this).parents('.fancy-combo-box').find('input:text')
			$(this).parents('.fancy-combo-box').attr("val", val)
			$(this).parents('.fancy-combo-box').find('input:hidden').val(val)
			_$textInput.val($(this).text())
			_$textInput.change()
			$(this).parents('.entries-overlay').addClass('hidden')
			e.stopPropagation()
		})
		$('.fancy-combo-box').mouseleave(function() {
			$(this).find('.entries-overlay').addClass('hidden')
		})
	})

    $.prototype.blink = function(numBlinks) {
    	var count = 0
    	$elt = $(this)
    	var id = setInterval(function() {
    		$elt.toggleClass('hidden')
    		count++
    		if (count == numBlinks) {
                clearInterval(id)
                $elt.removeClass('hidden')
            }
    	}, 400)
    }
    w.tck = c /*Creating the namespace tck for all this*/
})(window)
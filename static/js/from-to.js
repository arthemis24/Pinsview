/*!
 * Name:        from-to
 * Version:     1.0
 * Description: Manage date input of a period using jQuery UI Datepicker.
 *              Its makes sure the end date is at least equals to the start date
 * Author:      Kom Sihon
 * Support:     http://d-krypt.com
 *
 * Depends:
 *      jquery.js http://jquery.org
 *
 * Date: Wed May 10 15:13:18 2013 -0500
 */
(function(c) {    
    c.setupPeriodChooser = function(options) {
        var fromOptions = {},
            toOptions = {}
        if (options.altFormat) {
            fromOptions.altFormat = options.altFormat
            toOptions.altFormat = options.altFormat
        }
        if (options.dateFormat) {
            fromOptions.dateFormat = options.dateFormat
            toOptions.dateFormat = options.dateFormat
        }
        if (options.minDate) {
            fromOptions.minDate = options.minDate
            toOptions.minDate = options.minDate
        }
        if (options.fromAltFieldSelector) fromOptions.altField = options.fromAltFieldSelector
        if (options.toAltFieldSelector) toOptions.altField = options.toAltFieldSelector
        $(options.fromSelector).datepicker(fromOptions)
        $(options.toSelector).datepicker(toOptions)
        $(options.fromSelector).change(function() {
            var moveOutMin = $(this).datepicker('getDate')
            if (!options.equalityAuthorized) moveOutMin.setDate(moveOutMin.getDate() + 1)
            $(options.toSelector).datepicker("option", "minDate", moveOutMin)
        })
        $(options.toSelector).change(function() {
            var moveInMax = $(this).datepicker('getDate')
            $(options.fromSelector).datepicker("option", "maxDate", moveInMax)
        })
    }
})(ikwen)
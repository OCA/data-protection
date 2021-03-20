odoo.define('website_contact_extend.success_page', function (require) {
    "use strict";

    var ajax = require("web.ajax");

    // function check_user_exists(){
    // }

    $(document).on('blur', '.input_email_from', function (ev) {
        var email_from = $('.input_email_from').val();
        var company_name = $('.input_company').val();

        return ajax.jsonRpc('/check_user_exists', 'call', {
            email_from:  email_from,
            company_name: company_name,
        }).then(function (res) {
            var contactus_page = "/contactus-thank-you";
            if(res){
                contactus_page = "/contact-us-form-review";
            }
            $('form[action="/website_form/"]').attr('data-success_page',contactus_page);
        });
    });

    $(document).on('blur', '.input_company', function (ev) {
        var email_from = $('.input_email_from').val();
        var company_name = $('.input_company').val();

        return ajax.jsonRpc('/check_user_exists', 'call', {
            email_from:  email_from,
            company_name: company_name,
        }).then(function (res) {
            var contactus_page = "/contactus-thank-you";
            if(res){
                contactus_page = "/contact-us-form-review";
            }
            $('form[action="/website_form/"]').attr('data-success_page',contactus_page);
        });
    });

});

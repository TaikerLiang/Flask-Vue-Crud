// note: Каким-то образом получилось, что не смотря на то, что сообщение chrome.tabs.sendMessage из headers.js
//  было отправлено раньше загрузки этого скрипта, оно все-равно попало в обработчик ниже
//  console.log('Earlier recaptcha injection');

chrome.runtime.onMessage.addListener(function(request, sender, sendResponse) {
    if (typeof request.type !== 'undefined') {
        if (request.type === 'recaptcha3OriginalCallback') {
            delete request.type;

            var lastOriginalOnloadMethodName;
            lastOriginalOnloadMethodName = request.lastOriginalOnloadMethodName;

            // console.log('lastOriginalOnloadMethodName in injection', lastOriginalOnloadMethodName );

            // К этому моменту мы уже успели получить сообщение, содержащее lastOriginalOnloadMethodName
            var script = document.createElement('script');
            script.src = chrome.runtime.getURL('/js/recaptcha3_object_interceptor_callback.js');
            if (lastOriginalOnloadMethodName) {
                script.dataset['originalCallback'] = JSON.stringify(lastOriginalOnloadMethodName);
            }
            script.onload = function() {
                this.remove();
            };
            (document.head || document.documentElement).appendChild(script);
            // sendResponse(request);

            // console.log('lastOriginalOnloadMethodName KNOWN!', lastOriginalOnloadMethodName );

            /*
            script = document.getElementById('XYU');
            if (typeof script !== 'undefined') {
                script.dataset['originalCallback'] = JSON.stringify(lastOriginalOnloadMethodName);
                script.dataset['parameters'] = JSON.stringify('XYU!');

                console.log('script.dataset', script.dataset);
                console.log('script.dataset[\'originalCallback\']', script.dataset['originalCallback']);
            }
             */

            // setInterval(function () {
            // console.log('POSTING MESSSAGEEE BACK!');
            //     window.postMessage(
            //         {
            //             receiver: 'recaptchaObjectInterceptor',
            //             type: 'recaptcha3OriginalCallback',
            //             lastOriginalOnloadMethodName: lastOriginalOnloadMethodName,
            //         },
            //         window.location.href
            //     );
            // }, 1);
        }
    }
});

/*
window.addEventListener('message', function(event) {
    if (!event.data
        || typeof event.data.receiver == 'undefined'
        || event.data.receiver != 'recaptchaObjectInterceptor') {

        // this message is not for us
        return;
    }

    var data = event.data;

    if (data.type === 'getRecaptcha3OriginalCallback') {
        // lastOriginalOnloadMethodName = event.data.lastOriginalOnloadMethodName;

        console.log('POSTING MESSSAGEEE!');
        window.postMessage(
            {
                receiver: 'recaptchaObjectInterceptor',
                type: 'recaptcha3OriginalCallback',
                lastOriginalOnloadMethodName: lastOriginalOnloadMethodName,
            },
            window.location.href
        );
    }
});
 */

initGlobalStatus(function (items) {
    // check if we need to solve the recaptcha v3
    if (items.enable
        && items.solve_recaptcha3
        && !currentHostnameWhiteBlackListedOut(items)) {

        // К этому моменту мы уже успели получить сообщение, содержащее lastOriginalOnloadMethodName
        var script = document.createElement('script');
        script.src = chrome.runtime.getURL('/js/recaptcha3_object_interceptor.js');
        /*
        if (lastOriginalOnloadMethodName) {
            script.dataset['originalCallback'] = JSON.stringify(lastOriginalOnloadMethodName);
        }
         */
        script.onload = function() {
            this.remove();
        };
        (document.head || document.documentElement).appendChild(script);

        /*
        chrome.runtime.onMessage.addListener(function(request, sender, sendResponse) {
            if (typeof request.type !== 'undefined') {
                // todo: remove it
                // console.log('request recaptchaApiScriptRequested', request);

                if (request.type == 'recaptchaApiScriptRequested') {
                    delete request.type;

                    console.log('lastOriginalOnloadMethodName in injection', lastOriginalOnloadMethodName );

                    // К этому моменту мы уже успели получить сообщение, содержащее lastOriginalOnloadMethodName
                    var script = document.createElement('script');
                    script.src = chrome.runtime.getURL('/js/recaptcha3_object_interceptor_callback.js');
                    if (lastOriginalOnloadMethodName) {
                        script.dataset['originalCallback'] = JSON.stringify(lastOriginalOnloadMethodName);
                    }
                    script.onload = function() {
                        this.remove();
                    };
                    (document.head || document.documentElement).appendChild(script);
                }
            }
        });
         */

        /*
        window.addEventListener('message', function(event) {
            // console.log('message in RECAPTCHA OBJECT INTERCEPTOR received');
            // console.log(event);

            if (!event.data
                || typeof event.data.receiver == 'undefined'
                || event.data.receiver != 'recaptchaObjectInterceptor') {

                // this message is not for us
                return;
            }

            var data = event.data;

            // т.к. сообщения все внутри одного window и даже не выходят за рамки iframe,
            // то проблем с конкурентностью быть не должно
            // каждый слушает только свои сообщения и отправляет только своему слушателю

            if (data.type === 'recaptcha3OriginalCallback') {
                lastOriginalOnloadMethodName = event.data.lastOriginalOnloadMethodName;

                console.log('Remembering original onLoad method ' + lastOriginalOnloadMethodName);
            }
        });
         */

        /*
        return;

        chrome.runtime.onMessage.addListener(function(request, sender, sendResponse) {
            if (typeof request.type !== 'undefined') {
                // todo: remove it
                // console.log('request recaptchaApiScriptRequested', request);

                if (request.type == 'recaptchaApiScriptRequested') {
                    delete request.type;

                    // forwarding recaptchaApiScriptRequested request parameters to the interceptor script
                    var parameters = request;

                    // adding recaptcha3_object_inteceptor.js to the web page
                    // which works in the web page scope
                    var script = document.createElement('script');
                    script.dataset['parameters'] = JSON.stringify(parameters);
                    script.src = chrome.runtime.getURL('/js/recaptcha3_object_interceptor.js');
                    script.onload = function() {
                        this.remove();
                    };
                    (document.head || document.documentElement).appendChild(script);
                }
            }
        });
        */
    }
});

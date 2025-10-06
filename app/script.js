// comment out irrelevant stuff
Java.perform(()=>{
// let LicenseManager = Java.use("io.hextree.fridatarget.LicenseManager");
// LicenseManager["isLicenseStillValid"].implementation = function (context, unixTimestamp) {
//     console.log(`LicenseManager.isLicenseStillValid is called: context=${context}, unixTimestamp=${unixTimestamp}`);
//     this["isLicenseStillValid"](context, 10000);
// };



let sslbypass = Java.use("com.android.org.conscrypt.Platform");
    sslbypass["checkServerTrusted"].overload('javax.net.ssl.X509TrustManager', '[Ljava.security.cert.X509Certificate;', 'java.lang.String', 'com.android.org.conscrypt.ConscryptEngine')
                                .implementation = function () {
    console.log(`conscryptPlatform.checkServerTrusted is called`)};

})
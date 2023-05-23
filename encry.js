//
//
// p = r.a.enc.Utf8.parse("6f00cd9cade84e52"), l = r.a.enc.Utf8.parse("25d82196341548ef"), m = function m(e, t, n) {
//             var a = new Date().getTime().toString();
//             console.log(a);
//             var c = r.a.enc.Utf8.parse(a), u = r.a.AES.encrypt(c, p, {
//                 iv: l,
//                 mode: r.a.mode.CBC,
//                 padding: r.a.pad.Pkcs7
//             }), d = r.a.enc.Base64.stringify(u.ciphertext);
//             return new Promise(function(c, r) {
//                 o.a.getStorage({
//                     key: "token",
//                     success: function success(r) {
//                         c(o.a.request({
//                             url: "".concat(i, "/user/book/"),
//                             method: "POST",
//                             header: {
//                                 "Content-Type": "application/json",
//                                 token: r.data,
//                                 resultJSON: a,
//                                 resultJSONSignature: d
//                             },
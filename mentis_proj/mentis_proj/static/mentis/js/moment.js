!function(e, t) {
    "object" == typeof exports && "undefined" != typeof module ? module.exports = t() : "function" == typeof define && define.amd ? define(t) : e.moment = t()
}(this, function() {
    "use strict";
    var e, i;
    function p() {
        return e.apply(null, arguments)
    }
    function h(e) {
        return e instanceof Array || "[object Array]" === Object.prototype.toString.call(e)
    }
    function d(e) {
        return null != e && "[object Object]" === Object.prototype.toString.call(e)
    }
    function v(e, t) {
        return Object.prototype.hasOwnProperty.call(e, t)
    }
    function o(e) {
        if (Object.getOwnPropertyNames)
            return 0 === Object.getOwnPropertyNames(e).length;
        var t;
        for (t in e)
            if (v(e, t))
                return;
        return 1
    }
    function c(e) {
        return void 0 === e
    }
    function f(e) {
        return "number" == typeof e || "[object Number]" === Object.prototype.toString.call(e)
    }
    function m(e) {
        return e instanceof Date || "[object Date]" === Object.prototype.toString.call(e)
    }
    function _(e, t) {
        for (var n = [], s = 0; s < e.length; ++s)
            n.push(t(e[s], s));
        return n
    }
    function y(e, t) {
        for (var n in t)
            v(t, n) && (e[n] = t[n]);
        return v(t, "toString") && (e.toString = t.toString),
        v(t, "valueOf") && (e.valueOf = t.valueOf),
        e
    }
    function g(e, t, n, s) {
        return Ot(e, t, n, s, !0).utc()
    }
    function k(e) {
        return null == e._pf && (e._pf = {
            empty: !1,
            unusedTokens: [],
            unusedInput: [],
            overflow: -2,
            charsLeftOver: 0,
            nullInput: !1,
            invalidEra: null,
            invalidMonth: null,
            invalidFormat: !1,
            userInvalidated: !1,
            iso: !1,
            parsedDateParts: [],
            era: null,
            meridiem: null,
            rfc2822: !1,
            weekdayMismatch: !1
        }),
        e._pf
    }
    function w(e) {
        if (null == e._isValid) {
            var t = k(e)
              , n = i.call(t.parsedDateParts, function(e) {
                return null != e
            })
              , s = !isNaN(e._d.getTime()) && t.overflow < 0 && !t.empty && !t.invalidEra && !t.invalidMonth && !t.invalidWeekday && !t.weekdayMismatch && !t.nullInput && !t.invalidFormat && !t.userInvalidated && (!t.meridiem || t.meridiem && n);
            if (e._strict && (s = s && 0 === t.charsLeftOver && 0 === t.unusedTokens.length && void 0 === t.bigHour),
            null != Object.isFrozen && Object.isFrozen(e))
                return s;
            e._isValid = s
        }
        return e._isValid
    }
    function M(e) {
        var t = g(NaN);
        return null != e ? y(k(t), e) : k(t).userInvalidated = !0,
        t
    }
    i = Array.prototype.some ? Array.prototype.some : function(e) {
        for (var t = Object(this), n = t.length >>> 0, s = 0; s < n; s++)
            if (s in t && e.call(this, t[s], s, t))
                return !0;
        return !1
    }
    ;
    var r = p.momentProperties = []
      , t = !1;
    function D(e, t) {
        var n, s, i;
        if (c(t._isAMomentObject) || (e._isAMomentObject = t._isAMomentObject),
        c(t._i) || (e._i = t._i),
        c(t._f) || (e._f = t._f),
        c(t._l) || (e._l = t._l),
        c(t._strict) || (e._strict = t._strict),
        c(t._tzm) || (e._tzm = t._tzm),
        c(t._isUTC) || (e._isUTC = t._isUTC),
        c(t._offset) || (e._offset = t._offset),
        c(t._pf) || (e._pf = k(t)),
        c(t._locale) || (e._locale = t._locale),
        0 < r.length)
            for (n = 0; n < r.length; n++)
                c(i = t[s = r[n]]) || (e[s] = i);
        return e
    }
    function S(e) {
        D(this, e),
        this._d = new Date(null != e._d ? e._d.getTime() : NaN),
        this.isValid() || (this._d = new Date(NaN)),
        !1 === t && (t = !0,
        p.updateOffset(this),
        t = !1)
    }
    function Y(e) {
        return e instanceof S || null != e && null != e._isAMomentObject
    }
    function u(e) {
        !1 === p.suppressDeprecationWarnings && "undefined" != typeof console && console.warn && console.warn("Deprecation warning: " + e)
    }
    function n(i, r) {
        var a = !0;
        return y(function() {
            if (null != p.deprecationHandler && p.deprecationHandler(null, i),
            a) {
                for (var e, t, n = [], s = 0; s < arguments.length; s++) {
                    if (e = "",
                    "object" == typeof arguments[s]) {
                        for (t in e += "\n[" + s + "] ",
                        arguments[0])
                            v(arguments[0], t) && (e += t + ": " + arguments[0][t] + ", ");
                        e = e.slice(0, -2)
                    } else
                        e = arguments[s];
                    n.push(e)
                }
                u(i + "\nArguments: " + Array.prototype.slice.call(n).join("") + "\n" + (new Error).stack),
                a = !1
            }
            return r.apply(this, arguments)
        }, r)
    }
    var s, a = {};
    function l(e, t) {
        null != p.deprecationHandler && p.deprecationHandler(e, t),
        a[e] || (u(t),
        a[e] = !0)
    }
    function O(e) {
        return "undefined" != typeof Function && e instanceof Function || "[object Function]" === Object.prototype.toString.call(e)
    }
    function b(e, t) {
        var n, s = y({}, e);
        for (n in t)
            v(t, n) && (d(e[n]) && d(t[n]) ? (s[n] = {},
            y(s[n], e[n]),
            y(s[n], t[n])) : null != t[n] ? s[n] = t[n] : delete s[n]);
        for (n in e)
            v(e, n) && !v(t, n) && d(e[n]) && (s[n] = y({}, s[n]));
        return s
    }
    function x(e) {
        null != e && this.set(e)
    }
    function T(e, t, n) {
        var s = "" + Math.abs(e)
          , i = t - s.length;
        return (0 <= e ? n ? "+" : "" : "-") + Math.pow(10, Math.max(0, i)).toString().substr(1) + s
    }
    p.suppressDeprecationWarnings = !1,
    p.deprecationHandler = null,
    s = Object.keys ? Object.keys : function(e) {
        var t, n = [];
        for (t in e)
            v(e, t) && n.push(t);
        return n
    }
    ;
    var N = /(\[[^\[]*\])|(\\)?([Hh]mm(ss)?|Mo|MM?M?M?|Do|DDDo|DD?D?D?|ddd?d?|do?|w[o|w]?|W[o|W]?|Qo?|N{1,5}|YYYYYY|YYYYY|YYYY|YY|y{2,4}|yo?|gg(ggg?)?|GG(GGG?)?|e|E|a|A|hh?|HH?|kk?|mm?|ss?|S{1,9}|x|X|zz?|ZZ?|.)/g
      , P = /(\[[^\[]*\])|(\\)?(LTS|LT|LL?L?L?|l{1,4})/g
      , R = {}
      , W = {};
    function C(e, t, n, s) {
        var i = "string" == typeof s ? function() {
            return this[s]()
        }
        : s;
        e && (W[e] = i),
        t && (W[t[0]] = function() {
            return T(i.apply(this, arguments), t[1], t[2])
        }
        ),
        n && (W[n] = function() {
            return this.localeData().ordinal(i.apply(this, arguments), e)
        }
        )
    }
    function U(e, t) {
        return e.isValid() ? (t = H(t, e.localeData()),
        R[t] = R[t] || function(s) {
            for (var e, i = s.match(N), t = 0, r = i.length; t < r; t++)
                W[i[t]] ? i[t] = W[i[t]] : i[t] = (e = i[t]).match(/\[[\s\S]/) ? e.replace(/^\[|\]$/g, "") : e.replace(/\\/g, "");
            return function(e) {
                for (var t = "", n = 0; n < r; n++)
                    t += O(i[n]) ? i[n].call(e, s) : i[n];
                return t
            }
        }(t),
        R[t](e)) : e.localeData().invalidDate()
    }
    function H(e, t) {
        var n = 5;
        function s(e) {
            return t.longDateFormat(e) || e
        }
        for (P.lastIndex = 0; 0 <= n && P.test(e); )
            e = e.replace(P, s),
            P.lastIndex = 0,
            --n;
        return e
    }
    var F = {};
    function L(e, t) {
        var n = e.toLowerCase();
        F[n] = F[n + "s"] = F[t] = e
    }
    function V(e) {
        return "string" == typeof e ? F[e] || F[e.toLowerCase()] : void 0
    }
    function G(e) {
        var t, n, s = {};
        for (n in e)
            v(e, n) && (t = V(n)) && (s[t] = e[n]);
        return s
    }
    var E = {};
    function A(e, t) {
        E[e] = t
    }
    function j(e) {
        return e % 4 == 0 && e % 100 != 0 || e % 400 == 0
    }
    function I(e) {
        return e < 0 ? Math.ceil(e) || 0 : Math.floor(e)
    }
    function Z(e) {
        var t = +e
          , n = 0;
        return 0 != t && isFinite(t) && (n = I(t)),
        n
    }
    function z(t, n) {
        return function(e) {
            return null != e ? (q(this, t, e),
            p.updateOffset(this, n),
            this) : $(this, t)
        }
    }
    function $(e, t) {
        return e.isValid() ? e._d["get" + (e._isUTC ? "UTC" : "") + t]() : NaN
    }
    function q(e, t, n) {
        e.isValid() && !isNaN(n) && ("FullYear" === t && j(e.year()) && 1 === e.month() && 29 === e.date() ? (n = Z(n),
        e._d["set" + (e._isUTC ? "UTC" : "") + t](n, e.month(), be(n, e.month()))) : e._d["set" + (e._isUTC ? "UTC" : "") + t](n))
    }
    var B, J = /\d/, Q = /\d\d/, X = /\d{3}/, K = /\d{4}/, ee = /[+-]?\d{6}/, te = /\d\d?/, ne = /\d\d\d\d?/, se = /\d\d\d\d\d\d?/, ie = /\d{1,3}/, re = /\d{1,4}/, ae = /[+-]?\d{1,6}/, oe = /\d+/, ue = /[+-]?\d+/, le = /Z|[+-]\d\d:?\d\d/gi, he = /Z|[+-]\d\d(?::?\d\d)?/gi, de = /[0-9]{0,256}['a-z\u00A0-\u05FF\u0700-\uD7FF\uF900-\uFDCF\uFDF0-\uFF07\uFF10-\uFFEF]{1,256}|[\u0600-\u06FF\/]{1,256}(\s*?[\u0600-\u06FF]{1,256}){1,2}/i;
    function ce(e, n, s) {
        B[e] = O(n) ? n : function(e, t) {
            return e && s ? s : n
        }
    }
    function fe(e) {
        return e.replace(/[-\/\\^$*+?.()|[\]{}]/g, "\\$&")
    }
    B = {};
    var me = {};
    function _e(e, n) {
        var t, s = n;
        for ("string" == typeof e && (e = [e]),
        f(n) && (s = function(e, t) {
            t[n] = Z(e)
        }
        ),
        t = 0; t < e.length; t++)
            me[e[t]] = s
    }
    function ye(e, i) {
        _e(e, function(e, t, n, s) {
            n._w = n._w || {},
            i(e, n._w, n, s)
        })
    }
    var ge, we = 0, pe = 1, ve = 2, ke = 3, Me = 4, De = 5, Se = 6, Ye = 7, Oe = 8;
    function be(e, t) {
        if (isNaN(e) || isNaN(t))
            return NaN;
        var n = (t % 12 + 12) % 12;
        return e += (t - n) / 12,
        1 == n ? j(e) ? 29 : 28 : 31 - n % 7 % 2
    }
    ge = Array.prototype.indexOf ? Array.prototype.indexOf : function(e) {
        for (var t = 0; t < this.length; ++t)
            if (this[t] === e)
                return t;
        return -1
    }
    ,
    C("M", ["MM", 2], "Mo", function() {
        return this.month() + 1
    }),
    C("MMM", 0, 0, function(e) {
        return this.localeData().monthsShort(this, e)
    }),
    C("MMMM", 0, 0, function(e) {
        return this.localeData().months(this, e)
    }),
    L("month", "M"),
    A("month", 8),
    ce("M", te),
    ce("MM", te, Q),
    ce("MMM", function(e, t) {
        return t.monthsShortRegex(e)
    }),
    ce("MMMM", function(e, t) {
        return t.monthsRegex(e)
    }),
    _e(["M", "MM"], function(e, t) {
        t[pe] = Z(e) - 1
    }),
    _e(["MMM", "MMMM"], function(e, t, n, s) {
        var i = n._locale.monthsParse(e, s, n._strict);
        null != i ? t[pe] = i : k(n).invalidMonth = e
    });
    var xe = "January_February_March_April_May_June_July_August_September_October_November_December".split("_")
      , Te = "Jan_Feb_Mar_Apr_May_Jun_Jul_Aug_Sep_Oct_Nov_Dec".split("_")
      , Ne = /D[oD]?(\[[^\[\]]*\]|\s)+MMMM?/
      , Pe = de
      , Re = de;
    function We(e, t) {
        var n;
        if (!e.isValid())
            return e;
        if ("string" == typeof t)
            if (/^\d+$/.test(t))
                t = Z(t);
            else if (!f(t = e.localeData().monthsParse(t)))
                return e;
        return n = Math.min(e.date(), be(e.year(), t)),
        e._d["set" + (e._isUTC ? "UTC" : "") + "Month"](t, n),
        e
    }
    function Ce(e) {
        return null != e ? (We(this, e),
        p.updateOffset(this, !0),
        this) : $(this, "Month")
    }
    function Ue() {
        function e(e, t) {
            return t.length - e.length
        }
        for (var t, n = [], s = [], i = [], r = 0; r < 12; r++)
            t = g([2e3, r]),
            n.push(this.monthsShort(t, "")),
            s.push(this.months(t, "")),
            i.push(this.months(t, "")),
            i.push(this.monthsShort(t, ""));
        for (n.sort(e),
        s.sort(e),
        i.sort(e),
        r = 0; r < 12; r++)
            n[r] = fe(n[r]),
            s[r] = fe(s[r]);
        for (r = 0; r < 24; r++)
            i[r] = fe(i[r]);
        this._monthsRegex = new RegExp("^(" + i.join("|") + ")","i"),
        this._monthsShortRegex = this._monthsRegex,
        this._monthsStrictRegex = new RegExp("^(" + s.join("|") + ")","i"),
        this._monthsShortStrictRegex = new RegExp("^(" + n.join("|") + ")","i")
    }
    function He(e) {
        return j(e) ? 366 : 365
    }
    C("Y", 0, 0, function() {
        var e = this.year();
        return e <= 9999 ? T(e, 4) : "+" + e
    }),
    C(0, ["YY", 2], 0, function() {
        return this.year() % 100
    }),
    C(0, ["YYYY", 4], 0, "year"),
    C(0, ["YYYYY", 5], 0, "year"),
    C(0, ["YYYYYY", 6, !0], 0, "year"),
    L("year", "y"),
    A("year", 1),
    ce("Y", ue),
    ce("YY", te, Q),
    ce("YYYY", re, K),
    ce("YYYYY", ae, ee),
    ce("YYYYYY", ae, ee),
    _e(["YYYYY", "YYYYYY"], we),
    _e("YYYY", function(e, t) {
        t[we] = 2 === e.length ? p.parseTwoDigitYear(e) : Z(e)
    }),
    _e("YY", function(e, t) {
        t[we] = p.parseTwoDigitYear(e)
    }),
    _e("Y", function(e, t) {
        t[we] = parseInt(e, 10)
    }),
    p.parseTwoDigitYear = function(e) {
        return Z(e) + (68 < Z(e) ? 1900 : 2e3)
    }
    ;
    var Fe = z("FullYear", !0);
    function Le(e) {
        var t, n;
        return e < 100 && 0 <= e ? ((n = Array.prototype.slice.call(arguments))[0] = e + 400,
        t = new Date(Date.UTC.apply(null, n)),
        isFinite(t.getUTCFullYear()) && t.setUTCFullYear(e)) : t = new Date(Date.UTC.apply(null, arguments)),
        t
    }
    function Ve(e, t, n) {
        var s = 7 + t - n;
        return s - (7 + Le(e, 0, s).getUTCDay() - t) % 7 - 1
    }
    function Ge(e, t, n, s, i) {
        var r, a = 1 + 7 * (t - 1) + (7 + n - s) % 7 + Ve(e, s, i), o = a <= 0 ? He(r = e - 1) + a : a > He(e) ? (r = e + 1,
        a - He(e)) : (r = e,
        a);
        return {
            year: r,
            dayOfYear: o
        }
    }
    function Ee(e, t, n) {
        var s, i, r = Ve(e.year(), t, n), a = Math.floor((e.dayOfYear() - r - 1) / 7) + 1;
        return a < 1 ? s = a + Ae(i = e.year() - 1, t, n) : a > Ae(e.year(), t, n) ? (s = a - Ae(e.year(), t, n),
        i = e.year() + 1) : (i = e.year(),
        s = a),
        {
            week: s,
            year: i
        }
    }
    function Ae(e, t, n) {
        var s = Ve(e, t, n)
          , i = Ve(e + 1, t, n);
        return (He(e) - s + i) / 7
    }
    function je(e, t) {
        return e.slice(t, 7).concat(e.slice(0, t))
    }
    C("w", ["ww", 2], "wo", "week"),
    C("W", ["WW", 2], "Wo", "isoWeek"),
    L("week", "w"),
    L("isoWeek", "W"),
    A("week", 5),
    A("isoWeek", 5),
    ce("w", te),
    ce("ww", te, Q),
    ce("W", te),
    ce("WW", te, Q),
    ye(["w", "ww", "W", "WW"], function(e, t, n, s) {
        t[s.substr(0, 1)] = Z(e)
    }),
    C("d", 0, "do", "day"),
    C("dd", 0, 0, function(e) {
        return this.localeData().weekdaysMin(this, e)
    }),
    C("ddd", 0, 0, function(e) {
        return this.localeData().weekdaysShort(this, e)
    }),
    C("dddd", 0, 0, function(e) {
        return this.localeData().weekdays(this, e)
    }),
    C("e", 0, 0, "weekday"),
    C("E", 0, 0, "isoWeekday"),
    L("day", "d"),
    L("weekday", "e"),
    L("isoWeekday", "E"),
    A("day", 11),
    A("weekday", 11),
    A("isoWeekday", 11),
    ce("d", te),
    ce("e", te),
    ce("E", te),
    ce("dd", function(e, t) {
        return t.weekdaysMinRegex(e)
    }),
    ce("ddd", function(e, t) {
        return t.weekdaysShortRegex(e)
    }),
    ce("dddd", function(e, t) {
        return t.weekdaysRegex(e)
    }),
    ye(["dd", "ddd", "dddd"], function(e, t, n, s) {
        var i = n._locale.weekdaysParse(e, s, n._strict);
        null != i ? t.d = i : k(n).invalidWeekday = e
    }),
    ye(["d", "e", "E"], function(e, t, n, s) {
        t[s] = Z(e)
    });
    var Ie = "Sunday_Monday_Tuesday_Wednesday_Thursday_Friday_Saturday".split("_")
      , Ze = "Sun_Mon_Tue_Wed_Thu_Fri_Sat".split("_")
      , ze = "Su_Mo_Tu_We_Th_Fr_Sa".split("_")
      , $e = de
      , qe = de
      , Be = de;
    function Je() {
        function e(e, t) {
            return t.length - e.length
        }
        for (var t, n, s, i, r = [], a = [], o = [], u = [], l = 0; l < 7; l++)
            t = g([2e3, 1]).day(l),
            n = fe(this.weekdaysMin(t, "")),
            s = fe(this.weekdaysShort(t, "")),
            i = fe(this.weekdays(t, "")),
            r.push(n),
            a.push(s),
            o.push(i),
            u.push(n),
            u.push(s),
            u.push(i);
        r.sort(e),
        a.sort(e),
        o.sort(e),
        u.sort(e),
        this._weekdaysRegex = new RegExp("^(" + u.join("|") + ")","i"),
        this._weekdaysShortRegex = this._weekdaysRegex,
        this._weekdaysMinRegex = this._weekdaysRegex,
        this._weekdaysStrictRegex = new RegExp("^(" + o.join("|") + ")","i"),
        this._weekdaysShortStrictRegex = new RegExp("^(" + a.join("|") + ")","i"),
        this._weekdaysMinStrictRegex = new RegExp("^(" + r.join("|") + ")","i")
    }
    function Qe() {
        return this.hours() % 12 || 12
    }
    function Xe(e, t) {
        C(e, 0, 0, function() {
            return this.localeData().meridiem(this.hours(), this.minutes(), t)
        })
    }
    function Ke(e, t) {
        return t._meridiemParse
    }
    C("H", ["HH", 2], 0, "hour"),
    C("h", ["hh", 2], 0, Qe),
    C("k", ["kk", 2], 0, function() {
        return this.hours() || 24
    }),
    C("hmm", 0, 0, function() {
        return "" + Qe.apply(this) + T(this.minutes(), 2)
    }),
    C("hmmss", 0, 0, function() {
        return "" + Qe.apply(this) + T(this.minutes(), 2) + T(this.seconds(), 2)
    }),
    C("Hmm", 0, 0, function() {
        return "" + this.hours() + T(this.minutes(), 2)
    }),
    C("Hmmss", 0, 0, function() {
        return "" + this.hours() + T(this.minutes(), 2) + T(this.seconds(), 2)
    }),
    Xe("a", !0),
    Xe("A", !1),
    L("hour", "h"),
    A("hour", 13),
    ce("a", Ke),
    ce("A", Ke),
    ce("H", te),
    ce("h", te),
    ce("k", te),
    ce("HH", te, Q),
    ce("hh", te, Q),
    ce("kk", te, Q),
    ce("hmm", ne),
    ce("hmmss", se),
    ce("Hmm", ne),
    ce("Hmmss", se),
    _e(["H", "HH"], ke),
    _e(["k", "kk"], function(e, t, n) {
        var s = Z(e);
        t[ke] = 24 === s ? 0 : s
    }),
    _e(["a", "A"], function(e, t, n) {
        n._isPm = n._locale.isPM(e),
        n._meridiem = e
    }),
    _e(["h", "hh"], function(e, t, n) {
        t[ke] = Z(e),
        k(n).bigHour = !0
    }),
    _e("hmm", function(e, t, n) {
        var s = e.length - 2;
        t[ke] = Z(e.substr(0, s)),
        t[Me] = Z(e.substr(s)),
        k(n).bigHour = !0
    }),
    _e("hmmss", function(e, t, n) {
        var s = e.length - 4
          , i = e.length - 2;
        t[ke] = Z(e.substr(0, s)),
        t[Me] = Z(e.substr(s, 2)),
        t[De] = Z(e.substr(i)),
        k(n).bigHour = !0
    }),
    _e("Hmm", function(e, t, n) {
        var s = e.length - 2;
        t[ke] = Z(e.substr(0, s)),
        t[Me] = Z(e.substr(s))
    }),
    _e("Hmmss", function(e, t, n) {
        var s = e.length - 4
          , i = e.length - 2;
        t[ke] = Z(e.substr(0, s)),
        t[Me] = Z(e.substr(s, 2)),
        t[De] = Z(e.substr(i))
    });
    var et, tt = z("Hours", !0), nt = {
        calendar: {
            sameDay: "[Today at] LT",
            nextDay: "[Tomorrow at] LT",
            nextWeek: "dddd [at] LT",
            lastDay: "[Yesterday at] LT",
            lastWeek: "[Last] dddd [at] LT",
            sameElse: "L"
        },
        longDateFormat: {
            LTS: "h:mm:ss A",
            LT: "h:mm A",
            L: "DD/MM/YYYY",
            LL: "MMMM D, YYYY",
            LLL: "MMMM D, YYYY h:mm A",
            LLLL: "dddd, MMMM D, YYYY h:mm A"
        },
        invalidDate: "Invalid date",
        ordinal: "%d",
        dayOfMonthOrdinalParse: /\d{1,2}/,
        relativeTime: {
            future: "in %s",
            past: "%s ago",
            s: "a few seconds",
            ss: "%d seconds",
            m: "a minute",
            mm: "%d minutes",
            h: "an hour",
            hh: "%d hours",
            d: "a day",
            dd: "%d days",
            w: "a week",
            ww: "%d weeks",
            M: "a month",
            MM: "%d months",
            y: "a year",
            yy: "%d years"
        },
        months: xe,
        monthsShort: Te,
        week: {
            dow: 0,
            doy: 6
        },
        weekdays: Ie,
        weekdaysMin: ze,
        weekdaysShort: Ze,
        meridiemParse: /[ap]\.?m?\.?/i
    }, st = {}, it = {};
    function rt(e, t) {
        for (var n = Math.min(e.length, t.length), s = 0; s < n; s += 1)
            if (e[s] !== t[s])
                return s;
        return n
    }
    function at(e) {
        return e ? e.toLowerCase().replace("_", "-") : e
    }
    function ot(e) {
        var t = null;
        if (void 0 === st[e] && "undefined" != typeof module && module && module.exports)
            try {
                t = et._abbr,
                require("./locale/" + e),
                ut(t)
            } catch (t) {
                st[e] = null
            }
        return st[e]
    }
    function ut(e, t) {
        var n;
        return e && ((n = c(t) ? ht(e) : lt(e, t)) ? et = n : "undefined" != typeof console && console.warn && console.warn("Locale " + e + " not found. Did you forget to load it?")),
        et._abbr
    }
    function lt(e, t) {
        if (null === t)
            return delete st[e],
            null;
        var n, s = nt;
        if (t.abbr = e,
        null != st[e])
            l("defineLocaleOverride", "use moment.updateLocale(localeName, config) to change an existing locale. moment.defineLocale(localeName, config) should only be used for creating a new locale See http://momentjs.com/guides/#/warnings/define-locale/ for more info."),
            s = st[e]._config;
        else if (null != t.parentLocale)
            if (null != st[t.parentLocale])
                s = st[t.parentLocale]._config;
            else {
                if (null == (n = ot(t.parentLocale)))
                    return it[t.parentLocale] || (it[t.parentLocale] = []),
                    it[t.parentLocale].push({
                        name: e,
                        config: t
                    }),
                    null;
                s = n._config
            }
        return st[e] = new x(b(s, t)),
        it[e] && it[e].forEach(function(e) {
            lt(e.name, e.config)
        }),
        ut(e),
        st[e]
    }
    function ht(e) {
        var t;
        if (e && e._locale && e._locale._abbr && (e = e._locale._abbr),
        !e)
            return et;
        if (!h(e)) {
            if (t = ot(e))
                return t;
            e = [e]
        }
        return function(e) {
            for (var t, n, s, i, r = 0; r < e.length; ) {
                for (t = (i = at(e[r]).split("-")).length,
                n = (n = at(e[r + 1])) ? n.split("-") : null; 0 < t; ) {
                    if (s = ot(i.slice(0, t).join("-")))
                        return s;
                    if (n && n.length >= t && rt(i, n) >= t - 1)
                        break;
                    t--
                }
                r++
            }
            return et
        }(e)
    }
    function dt(e) {
        var t, n = e._a;
        return n && -2 === k(e).overflow && (t = n[pe] < 0 || 11 < n[pe] ? pe : n[ve] < 1 || n[ve] > be(n[we], n[pe]) ? ve : n[ke] < 0 || 24 < n[ke] || 24 === n[ke] && (0 !== n[Me] || 0 !== n[De] || 0 !== n[Se]) ? ke : n[Me] < 0 || 59 < n[Me] ? Me : n[De] < 0 || 59 < n[De] ? De : n[Se] < 0 || 999 < n[Se] ? Se : -1,
        k(e)._overflowDayOfYear && (t < we || ve < t) && (t = ve),
        k(e)._overflowWeeks && -1 === t && (t = Ye),
        k(e)._overflowWeekday && -1 === t && (t = Oe),
        k(e).overflow = t),
        e
    }
    var ct = /^\s*((?:[+-]\d{6}|\d{4})-(?:\d\d-\d\d|W\d\d-\d|W\d\d|\d\d\d|\d\d))(?:(T| )(\d\d(?::\d\d(?::\d\d(?:[.,]\d+)?)?)?)([+-]\d\d(?::?\d\d)?|\s*Z)?)?$/
      , ft = /^\s*((?:[+-]\d{6}|\d{4})(?:\d\d\d\d|W\d\d\d|W\d\d|\d\d\d|\d\d|))(?:(T| )(\d\d(?:\d\d(?:\d\d(?:[.,]\d+)?)?)?)([+-]\d\d(?::?\d\d)?|\s*Z)?)?$/
      , mt = /Z|[+-]\d\d(?::?\d\d)?/
      , _t = [["YYYYYY-MM-DD", /[+-]\d{6}-\d\d-\d\d/], ["YYYY-MM-DD", /\d{4}-\d\d-\d\d/], ["GGGG-[W]WW-E", /\d{4}-W\d\d-\d/], ["GGGG-[W]WW", /\d{4}-W\d\d/, !1], ["YYYY-DDD", /\d{4}-\d{3}/], ["YYYY-MM", /\d{4}-\d\d/, !1], ["YYYYYYMMDD", /[+-]\d{10}/], ["YYYYMMDD", /\d{8}/], ["GGGG[W]WWE", /\d{4}W\d{3}/], ["GGGG[W]WW", /\d{4}W\d{2}/, !1], ["YYYYDDD", /\d{7}/], ["YYYYMM", /\d{6}/, !1], ["YYYY", /\d{4}/, !1]]
      , yt = [["HH:mm:ss.SSSS", /\d\d:\d\d:\d\d\.\d+/], ["HH:mm:ss,SSSS", /\d\d:\d\d:\d\d,\d+/], ["HH:mm:ss", /\d\d:\d\d:\d\d/], ["HH:mm", /\d\d:\d\d/], ["HHmmss.SSSS", /\d\d\d\d\d\d\.\d+/], ["HHmmss,SSSS", /\d\d\d\d\d\d,\d+/], ["HHmmss", /\d\d\d\d\d\d/], ["HHmm", /\d\d\d\d/], ["HH", /\d\d/]]
      , gt = /^\/?Date\((-?\d+)/i
      , wt = /^(?:(Mon|Tue|Wed|Thu|Fri|Sat|Sun),?\s)?(\d{1,2})\s(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s(\d{2,4})\s(\d\d):(\d\d)(?::(\d\d))?\s(?:(UT|GMT|[ECMP][SD]T)|([Zz])|([+-]\d{4}))$/
      , pt = {
        UT: 0,
        GMT: 0,
        EDT: -240,
        EST: -300,
        CDT: -300,
        CST: -360,
        MDT: -360,
        MST: -420,
        PDT: -420,
        PST: -480
    };
    function vt(e) {
        var t, n, s, i, r, a, o = e._i, u = ct.exec(o) || ft.exec(o);
        if (u) {
            for (k(e).iso = !0,
            t = 0,
            n = _t.length; t < n; t++)
                if (_t[t][1].exec(u[1])) {
                    i = _t[t][0],
                    s = !1 !== _t[t][2];
                    break
                }
            if (null == i)
                return e._isValid = !1;
            if (u[3]) {
                for (t = 0,
                n = yt.length; t < n; t++)
                    if (yt[t][1].exec(u[3])) {
                        r = (u[2] || " ") + yt[t][0];
                        break
                    }
                if (null == r)
                    return e._isValid = !1
            }
            if (!s && null != r)
                return e._isValid = !1;
            if (u[4]) {
                if (!mt.exec(u[4]))
                    return e._isValid = !1;
                a = "Z"
            }
            e._f = i + (r || "") + (a || ""),
            St(e)
        } else
            e._isValid = !1
    }
    function kt(e) {
        var t, n, s, i, r, a, o, u, l, h, d, c, f = wt.exec(e._i.replace(/\([^)]*\)|[\n\t]/g, " ").replace(/(\s\s+)/g, " ").replace(/^\s\s*/, "").replace(/\s\s*$/, ""));
        if (f) {
            if (r = f[4],
            a = f[3],
            o = f[2],
            u = f[5],
            l = f[6],
            h = f[7],
            c = [(d = parseInt(r, 10)) <= 49 ? 2e3 + d : d <= 999 ? 1900 + d : d, Te.indexOf(a), parseInt(o, 10), parseInt(u, 10), parseInt(l, 10)],
            h && c.push(parseInt(h, 10)),
            s = t = c,
            i = e,
            (n = f[1]) && Ze.indexOf(n) !== new Date(s[0],s[1],s[2]).getDay() && (k(i).weekdayMismatch = !0,
            !void (i._isValid = !1)))
                return;
            e._a = t,
            e._tzm = function(e, t, n) {
                if (e)
                    return pt[e];
                if (t)
                    return 0;
                var s = parseInt(n, 10)
                  , i = s % 100;
                return (s - i) / 100 * 60 + i
            }(f[8], f[9], f[10]),
            e._d = Le.apply(null, e._a),
            e._d.setUTCMinutes(e._d.getUTCMinutes() - e._tzm),
            k(e).rfc2822 = !0
        } else
            e._isValid = !1
    }
    function Mt(e, t, n) {
        return null != e ? e : null != t ? t : n
    }
    function Dt(e) {
        var t, n, s, i, r, a, o, u, l, h, d, c, f, m, _ = [];
        if (!e._d) {
            var y = e
              , g = new Date(p.now())
              , w = y._useUTC ? [g.getUTCFullYear(), g.getUTCMonth(), g.getUTCDate()] : [g.getFullYear(), g.getMonth(), g.getDate()];
            for (e._w && null == e._a[ve] && null == e._a[pe] && (null != (a = (r = e)._w).GG || null != a.W || null != a.E ? (h = 1,
            d = 4,
            o = Mt(a.GG, r._a[we], Ee(bt(), 1, 4).year),
            u = Mt(a.W, 1),
            ((l = Mt(a.E, 1)) < 1 || 7 < l) && (f = !0)) : (h = r._locale._week.dow,
            d = r._locale._week.doy,
            m = Ee(bt(), h, d),
            o = Mt(a.gg, r._a[we], m.year),
            u = Mt(a.w, m.week),
            null != a.d ? ((l = a.d) < 0 || 6 < l) && (f = !0) : null != a.e ? (l = a.e + h,
            (a.e < 0 || 6 < a.e) && (f = !0)) : l = h),
            u < 1 || u > Ae(o, h, d) ? k(r)._overflowWeeks = !0 : null != f ? k(r)._overflowWeekday = !0 : (c = Ge(o, u, l, h, d),
            r._a[we] = c.year,
            r._dayOfYear = c.dayOfYear)),
            null != e._dayOfYear && (i = Mt(e._a[we], w[we]),
            (e._dayOfYear > He(i) || 0 === e._dayOfYear) && (k(e)._overflowDayOfYear = !0),
            n = Le(i, 0, e._dayOfYear),
            e._a[pe] = n.getUTCMonth(),
            e._a[ve] = n.getUTCDate()),
            t = 0; t < 3 && null == e._a[t]; ++t)
                e._a[t] = _[t] = w[t];
            for (; t < 7; t++)
                e._a[t] = _[t] = null == e._a[t] ? 2 === t ? 1 : 0 : e._a[t];
            24 === e._a[ke] && 0 === e._a[Me] && 0 === e._a[De] && 0 === e._a[Se] && (e._nextDay = !0,
            e._a[ke] = 0),
            e._d = (e._useUTC ? Le : function(e, t, n, s, i, r, a) {
                var o;
                return e < 100 && 0 <= e ? (o = new Date(e + 400,t,n,s,i,r,a),
                isFinite(o.getFullYear()) && o.setFullYear(e)) : o = new Date(e,t,n,s,i,r,a),
                o
            }
            ).apply(null, _),
            s = e._useUTC ? e._d.getUTCDay() : e._d.getDay(),
            null != e._tzm && e._d.setUTCMinutes(e._d.getUTCMinutes() - e._tzm),
            e._nextDay && (e._a[ke] = 24),
            e._w && void 0 !== e._w.d && e._w.d !== s && (k(e).weekdayMismatch = !0)
        }
    }
    function St(e) {
        if (e._f !== p.ISO_8601)
            if (e._f !== p.RFC_2822) {
                e._a = [],
                k(e).empty = !0;
                for (var t, n, s, i, r, a, o, u = "" + e._i, l = u.length, h = 0, d = H(e._f, e._locale).match(N) || [], c = 0; c < d.length; c++)
                    n = d[c],
                    (t = (u.match((w = e,
                    v(B, g = n) ? B[g](w._strict, w._locale) : new RegExp(fe(g.replace("\\", "").replace(/\\(\[)|\\(\])|\[([^\]\[]*)\]|\\(.)/g, function(e, t, n, s, i) {
                        return t || n || s || i
                    }))))) || [])[0]) && (0 < (s = u.substr(0, u.indexOf(t))).length && k(e).unusedInput.push(s),
                    u = u.slice(u.indexOf(t) + t.length),
                    h += t.length),
                    W[n] ? (t ? k(e).empty = !1 : k(e).unusedTokens.push(n),
                    r = n,
                    o = e,
                    null != (a = t) && v(me, r) && me[r](a, o._a, o, r)) : e._strict && !t && k(e).unusedTokens.push(n);
                k(e).charsLeftOver = l - h,
                0 < u.length && k(e).unusedInput.push(u),
                e._a[ke] <= 12 && !0 === k(e).bigHour && 0 < e._a[ke] && (k(e).bigHour = void 0),
                k(e).parsedDateParts = e._a.slice(0),
                k(e).meridiem = e._meridiem,
                e._a[ke] = (f = e._locale,
                m = e._a[ke],
                null == (_ = e._meridiem) ? m : null != f.meridiemHour ? f.meridiemHour(m, _) : (null != f.isPM && ((y = f.isPM(_)) && m < 12 && (m += 12),
                y || 12 !== m || (m = 0)),
                m)),
                null !== (i = k(e).era) && (e._a[we] = e._locale.erasConvertYear(i, e._a[we])),
                Dt(e),
                dt(e)
            } else
                kt(e);
        else
            vt(e);
        var f, m, _, y, g, w
    }
    function Yt(e) {
        var t, n, s, i, r, a, o, u = e._i, l = e._f;
        return e._locale = e._locale || ht(e._l),
        null === u || void 0 === l && "" === u ? M({
            nullInput: !0
        }) : ("string" == typeof u && (e._i = u = e._locale.preparse(u)),
        Y(u) ? new S(dt(u)) : (m(u) ? e._d = u : h(l) ? function(e) {
            var t, n, s, i, r, a, o = !1;
            if (0 === e._f.length)
                return k(e).invalidFormat = !0,
                e._d = new Date(NaN);
            for (i = 0; i < e._f.length; i++)
                r = 0,
                a = !1,
                t = D({}, e),
                null != e._useUTC && (t._useUTC = e._useUTC),
                t._f = e._f[i],
                St(t),
                w(t) && (a = !0),
                r += k(t).charsLeftOver,
                r += 10 * k(t).unusedTokens.length,
                k(t).score = r,
                o ? r < s && (s = r,
                n = t) : (null == s || r < s || a) && (s = r,
                n = t,
                a && (o = !0));
            y(e, n || t)
        }(e) : l ? St(e) : c(n = (t = e)._i) ? t._d = new Date(p.now()) : m(n) ? t._d = new Date(n.valueOf()) : "string" == typeof n ? (a = t,
        null === (o = gt.exec(a._i)) ? (vt(a),
        !1 === a._isValid && (delete a._isValid,
        kt(a),
        !1 === a._isValid && (delete a._isValid,
        a._strict ? a._isValid = !1 : p.createFromInputFallback(a)))) : a._d = new Date(+o[1])) : h(n) ? (t._a = _(n.slice(0), function(e) {
            return parseInt(e, 10)
        }),
        Dt(t)) : d(n) ? (s = t)._d || (r = void 0 === (i = G(s._i)).day ? i.date : i.day,
        s._a = _([i.year, i.month, r, i.hour, i.minute, i.second, i.millisecond], function(e) {
            return e && parseInt(e, 10)
        }),
        Dt(s)) : f(n) ? t._d = new Date(n) : p.createFromInputFallback(t),
        w(e) || (e._d = null),
        e))
    }
    function Ot(e, t, n, s, i) {
        var r, a = {};
        return !0 !== t && !1 !== t || (s = t,
        t = void 0),
        !0 !== n && !1 !== n || (s = n,
        n = void 0),
        (d(e) && o(e) || h(e) && 0 === e.length) && (e = void 0),
        a._isAMomentObject = !0,
        a._useUTC = a._isUTC = i,
        a._l = n,
        a._i = e,
        a._f = t,
        a._strict = s,
        (r = new S(dt(Yt(a))))._nextDay && (r.add(1, "d"),
        r._nextDay = void 0),
        r
    }
    function bt(e, t, n, s) {
        return Ot(e, t, n, s, !1)
    }
    p.createFromInputFallback = n("value provided is not in a recognized RFC2822 or ISO format. moment construction falls back to js Date(), which is not reliable across all browsers and versions. Non RFC2822/ISO date formats are discouraged and will be removed in an upcoming major release. Please refer to http://momentjs.com/guides/#/warnings/js-date/ for more info.", function(e) {
        e._d = new Date(e._i + (e._useUTC ? " UTC" : ""))
    }),
    p.ISO_8601 = function() {}
    ,
    p.RFC_2822 = function() {}
    ;
    var xt = n("moment().min is deprecated, use moment.max instead. http://momentjs.com/guides/#/warnings/min-max/", function() {
        var e = bt.apply(null, arguments);
        return this.isValid() && e.isValid() ? e < this ? this : e : M()
    })
      , Tt = n("moment().max is deprecated, use moment.min instead. http://momentjs.com/guides/#/warnings/min-max/", function() {
        var e = bt.apply(null, arguments);
        return this.isValid() && e.isValid() ? this < e ? this : e : M()
    });
    function Nt(e, t) {
        var n, s;
        if (1 === t.length && h(t[0]) && (t = t[0]),
        !t.length)
            return bt();
        for (n = t[0],
        s = 1; s < t.length; ++s)
            t[s].isValid() && !t[s][e](n) || (n = t[s]);
        return n
    }
    var Pt = ["year", "quarter", "month", "week", "day", "hour", "minute", "second", "millisecond"];
    function Rt(e) {
        var t = G(e)
          , n = t.year || 0
          , s = t.quarter || 0
          , i = t.month || 0
          , r = t.week || t.isoWeek || 0
          , a = t.day || 0
          , o = t.hour || 0
          , u = t.minute || 0
          , l = t.second || 0
          , h = t.millisecond || 0;
        this._isValid = function(e) {
            var t, n, s = !1;
            for (t in e)
                if (v(e, t) && (-1 === ge.call(Pt, t) || null != e[t] && isNaN(e[t])))
                    return !1;
            for (n = 0; n < Pt.length; ++n)
                if (e[Pt[n]]) {
                    if (s)
                        return !1;
                    parseFloat(e[Pt[n]]) !== Z(e[Pt[n]]) && (s = !0)
                }
            return !0
        }(t),
        this._milliseconds = +h + 1e3 * l + 6e4 * u + 1e3 * o * 60 * 60,
        this._days = +a + 7 * r,
        this._months = +i + 3 * s + 12 * n,
        this._data = {},
        this._locale = ht(),
        this._bubble()
    }
    function Wt(e) {
        return e instanceof Rt
    }
    function Ct(e) {
        return e < 0 ? -1 * Math.round(-1 * e) : Math.round(e)
    }
    function Ut(e, n) {
        C(e, 0, 0, function() {
            var e = this.utcOffset()
              , t = "+";
            return e < 0 && (e = -e,
            t = "-"),
            t + T(~~(e / 60), 2) + n + T(~~e % 60, 2)
        })
    }
    Ut("Z", ":"),
    Ut("ZZ", ""),
    ce("Z", he),
    ce("ZZ", he),
    _e(["Z", "ZZ"], function(e, t, n) {
        n._useUTC = !0,
        n._tzm = Ft(he, e)
    });
    var Ht = /([\+\-]|\d\d)/gi;
    function Ft(e, t) {
        var n, s, i = (t || "").match(e);
        return null === i ? null : 0 === (s = 60 * (n = ((i[i.length - 1] || []) + "").match(Ht) || ["-", 0, 0])[1] + Z(n[2])) ? 0 : "+" === n[0] ? s : -s
    }
    function Lt(e, t) {
        var n, s;
        return t._isUTC ? (n = t.clone(),
        s = (Y(e) || m(e) ? e.valueOf() : bt(e).valueOf()) - n.valueOf(),
        n._d.setTime(n._d.valueOf() + s),
        p.updateOffset(n, !1),
        n) : bt(e).local()
    }
    function Vt(e) {
        return -Math.round(e._d.getTimezoneOffset())
    }
    function Gt() {
        return !!this.isValid() && this._isUTC && 0 === this._offset
    }
    p.updateOffset = function() {}
    ;
    var Et = /^(-|\+)?(?:(\d*)[. ])?(\d+):(\d+)(?::(\d+)(\.\d*)?)?$/
      , At = /^(-|\+)?P(?:([-+]?[0-9,.]*)Y)?(?:([-+]?[0-9,.]*)M)?(?:([-+]?[0-9,.]*)W)?(?:([-+]?[0-9,.]*)D)?(?:T(?:([-+]?[0-9,.]*)H)?(?:([-+]?[0-9,.]*)M)?(?:([-+]?[0-9,.]*)S)?)?$/;
    function jt(e, t) {
        var n, s, i, r, a, o, u = e, l = null;
        return Wt(e) ? u = {
            ms: e._milliseconds,
            d: e._days,
            M: e._months
        } : f(e) || !isNaN(+e) ? (u = {},
        t ? u[t] = +e : u.milliseconds = +e) : (l = Et.exec(e)) ? (n = "-" === l[1] ? -1 : 1,
        u = {
            y: 0,
            d: Z(l[ve]) * n,
            h: Z(l[ke]) * n,
            m: Z(l[Me]) * n,
            s: Z(l[De]) * n,
            ms: Z(Ct(1e3 * l[Se])) * n
        }) : (l = At.exec(e)) ? (n = "-" === l[1] ? -1 : 1,
        u = {
            y: It(l[2], n),
            M: It(l[3], n),
            w: It(l[4], n),
            d: It(l[5], n),
            h: It(l[6], n),
            m: It(l[7], n),
            s: It(l[8], n)
        }) : null == u ? u = {} : "object" == typeof u && ("from"in u || "to"in u) && (r = bt(u.from),
        a = bt(u.to),
        i = r.isValid() && a.isValid() ? (a = Lt(a, r),
        r.isBefore(a) ? o = Zt(r, a) : ((o = Zt(a, r)).milliseconds = -o.milliseconds,
        o.months = -o.months),
        o) : {
            milliseconds: 0,
            months: 0
        },
        (u = {}).ms = i.milliseconds,
        u.M = i.months),
        s = new Rt(u),
        Wt(e) && v(e, "_locale") && (s._locale = e._locale),
        Wt(e) && v(e, "_isValid") && (s._isValid = e._isValid),
        s
    }
    function It(e, t) {
        var n = e && parseFloat(e.replace(",", "."));
        return (isNaN(n) ? 0 : n) * t
    }
    function Zt(e, t) {
        var n = {};
        return n.months = t.month() - e.month() + 12 * (t.year() - e.year()),
        e.clone().add(n.months, "M").isAfter(t) && --n.months,
        n.milliseconds = t - e.clone().add(n.months, "M"),
        n
    }
    function zt(s, i) {
        return function(e, t) {
            var n;
            return null === t || isNaN(+t) || (l(i, "moment()." + i + "(period, number) is deprecated. Please use moment()." + i + "(number, period). See http://momentjs.com/guides/#/warnings/add-inverted-param/ for more info."),
            n = e,
            e = t,
            t = n),
            $t(this, jt(e, t), s),
            this
        }
    }
    function $t(e, t, n, s) {
        var i = t._milliseconds
          , r = Ct(t._days)
          , a = Ct(t._months);
        e.isValid() && (s = null == s || s,
        a && We(e, $(e, "Month") + a * n),
        r && q(e, "Date", $(e, "Date") + r * n),
        i && e._d.setTime(e._d.valueOf() + i * n),
        s && p.updateOffset(e, r || a))
    }
    jt.fn = Rt.prototype,
    jt.invalid = function() {
        return jt(NaN)
    }
    ;
    var qt = zt(1, "add")
      , Bt = zt(-1, "subtract");
    function Jt(e) {
        return "string" == typeof e || e instanceof String
    }
    function Qt(e) {
        return Y(e) || m(e) || Jt(e) || f(e) || (n = h(t = e),
        s = !1,
        n && (s = 0 === t.filter(function(e) {
            return !f(e) && Jt(t)
        }).length),
        n && s) || function(e) {
            for (var t = d(e) && !o(e), n = !1, s = ["years", "year", "y", "months", "month", "M", "days", "day", "d", "dates", "date", "D", "hours", "hour", "h", "minutes", "minute", "m", "seconds", "second", "s", "milliseconds", "millisecond", "ms"], i = 0; i < s.length; i += 1)
                n = n || v(e, s[i]);
            return t && n
        }(e) || null == e;
        var t, n, s
    }
    function Xt(e, t) {
        if (e.date() < t.date())
            return -Xt(t, e);
        var n = 12 * (t.year() - e.year()) + (t.month() - e.month())
          , s = e.clone().add(n, "months");
        return -(n + (t - s < 0 ? (t - s) / (s - e.clone().add(n - 1, "months")) : (t - s) / (e.clone().add(1 + n, "months") - s))) || 0
    }
    function Kt(e) {
        var t;
        return void 0 === e ? this._locale._abbr : (null != (t = ht(e)) && (this._locale = t),
        this)
    }
    p.defaultFormat = "YYYY-MM-DDTHH:mm:ssZ",
    p.defaultFormatUtc = "YYYY-MM-DDTHH:mm:ss[Z]";
    var en = n("moment().lang() is deprecated. Instead, use moment().localeData() to get the language configuration. Use moment().locale() to change languages.", function(e) {
        return void 0 === e ? this.localeData() : this.locale(e)
    });
    function tn() {
        return this._locale
    }
    var nn = 126227808e5;
    function sn(e, t) {
        return (e % t + t) % t
    }
    function rn(e, t, n) {
        return e < 100 && 0 <= e ? new Date(e + 400,t,n) - nn : new Date(e,t,n).valueOf()
    }
    function an(e, t, n) {
        return e < 100 && 0 <= e ? Date.UTC(e + 400, t, n) - nn : Date.UTC(e, t, n)
    }
    function on(e, t) {
        return t.erasAbbrRegex(e)
    }
    function un() {
        for (var e = [], t = [], n = [], s = [], i = this.eras(), r = 0, a = i.length; r < a; ++r)
            t.push(fe(i[r].name)),
            e.push(fe(i[r].abbr)),
            n.push(fe(i[r].narrow)),
            s.push(fe(i[r].name)),
            s.push(fe(i[r].abbr)),
            s.push(fe(i[r].narrow));
        this._erasRegex = new RegExp("^(" + s.join("|") + ")","i"),
        this._erasNameRegex = new RegExp("^(" + t.join("|") + ")","i"),
        this._erasAbbrRegex = new RegExp("^(" + e.join("|") + ")","i"),
        this._erasNarrowRegex = new RegExp("^(" + n.join("|") + ")","i")
    }
    function ln(e, t) {
        C(0, [e, e.length], 0, t)
    }
    function hn(e, t, n, s, i) {
        var r;
        return null == e ? Ee(this, s, i).year : ((r = Ae(e, s, i)) < t && (t = r),
        function(e, t, n, s, i) {
            var r = Ge(e, t, n, s, i)
              , a = Le(r.year, 0, r.dayOfYear);
            return this.year(a.getUTCFullYear()),
            this.month(a.getUTCMonth()),
            this.date(a.getUTCDate()),
            this
        }
        .call(this, e, t, n, s, i))
    }
    C("N", 0, 0, "eraAbbr"),
    C("NN", 0, 0, "eraAbbr"),
    C("NNN", 0, 0, "eraAbbr"),
    C("NNNN", 0, 0, "eraName"),
    C("NNNNN", 0, 0, "eraNarrow"),
    C("y", ["y", 1], "yo", "eraYear"),
    C("y", ["yy", 2], 0, "eraYear"),
    C("y", ["yyy", 3], 0, "eraYear"),
    C("y", ["yyyy", 4], 0, "eraYear"),
    ce("N", on),
    ce("NN", on),
    ce("NNN", on),
    ce("NNNN", function(e, t) {
        return t.erasNameRegex(e)
    }),
    ce("NNNNN", function(e, t) {
        return t.erasNarrowRegex(e)
    }),
    _e(["N", "NN", "NNN", "NNNN", "NNNNN"], function(e, t, n, s) {
        var i = n._locale.erasParse(e, s, n._strict);
        i ? k(n).era = i : k(n).invalidEra = e
    }),
    ce("y", oe),
    ce("yy", oe),
    ce("yyy", oe),
    ce("yyyy", oe),
    ce("yo", function(e, t) {
        return t._eraYearOrdinalRegex || oe
    }),
    _e(["y", "yy", "yyy", "yyyy"], we),
    _e(["yo"], function(e, t, n, s) {
        var i;
        n._locale._eraYearOrdinalRegex && (i = e.match(n._locale._eraYearOrdinalRegex)),
        n._locale.eraYearOrdinalParse ? t[we] = n._locale.eraYearOrdinalParse(e, i) : t[we] = parseInt(e, 10)
    }),
    C(0, ["gg", 2], 0, function() {
        return this.weekYear() % 100
    }),
    C(0, ["GG", 2], 0, function() {
        return this.isoWeekYear() % 100
    }),
    ln("gggg", "weekYear"),
    ln("ggggg", "weekYear"),
    ln("GGGG", "isoWeekYear"),
    ln("GGGGG", "isoWeekYear"),
    L("weekYear", "gg"),
    L("isoWeekYear", "GG"),
    A("weekYear", 1),
    A("isoWeekYear", 1),
    ce("G", ue),
    ce("g", ue),
    ce("GG", te, Q),
    ce("gg", te, Q),
    ce("GGGG", re, K),
    ce("gggg", re, K),
    ce("GGGGG", ae, ee),
    ce("ggggg", ae, ee),
    ye(["gggg", "ggggg", "GGGG", "GGGGG"], function(e, t, n, s) {
        t[s.substr(0, 2)] = Z(e)
    }),
    ye(["gg", "GG"], function(e, t, n, s) {
        t[s] = p.parseTwoDigitYear(e)
    }),
    C("Q", 0, "Qo", "quarter"),
    L("quarter", "Q"),
    A("quarter", 7),
    ce("Q", J),
    _e("Q", function(e, t) {
        t[pe] = 3 * (Z(e) - 1)
    }),
    C("D", ["DD", 2], "Do", "date"),
    L("date", "D"),
    A("date", 9),
    ce("D", te),
    ce("DD", te, Q),
    ce("Do", function(e, t) {
        return e ? t._dayOfMonthOrdinalParse || t._ordinalParse : t._dayOfMonthOrdinalParseLenient
    }),
    _e(["D", "DD"], ve),
    _e("Do", function(e, t) {
        t[ve] = Z(e.match(te)[0])
    });
    var dn = z("Date", !0);
    C("DDD", ["DDDD", 3], "DDDo", "dayOfYear"),
    L("dayOfYear", "DDD"),
    A("dayOfYear", 4),
    ce("DDD", ie),
    ce("DDDD", X),
    _e(["DDD", "DDDD"], function(e, t, n) {
        n._dayOfYear = Z(e)
    }),
    C("m", ["mm", 2], 0, "minute"),
    L("minute", "m"),
    A("minute", 14),
    ce("m", te),
    ce("mm", te, Q),
    _e(["m", "mm"], Me);
    var cn = z("Minutes", !1);
    C("s", ["ss", 2], 0, "second"),
    L("second", "s"),
    A("second", 15),
    ce("s", te),
    ce("ss", te, Q),
    _e(["s", "ss"], De);
    var fn, mn, _n = z("Seconds", !1);
    for (C("S", 0, 0, function() {
        return ~~(this.millisecond() / 100)
    }),
    C(0, ["SS", 2], 0, function() {
        return ~~(this.millisecond() / 10)
    }),
    C(0, ["SSS", 3], 0, "millisecond"),
    C(0, ["SSSS", 4], 0, function() {
        return 10 * this.millisecond()
    }),
    C(0, ["SSSSS", 5], 0, function() {
        return 100 * this.millisecond()
    }),
    C(0, ["SSSSSS", 6], 0, function() {
        return 1e3 * this.millisecond()
    }),
    C(0, ["SSSSSSS", 7], 0, function() {
        return 1e4 * this.millisecond()
    }),
    C(0, ["SSSSSSSS", 8], 0, function() {
        return 1e5 * this.millisecond()
    }),
    C(0, ["SSSSSSSSS", 9], 0, function() {
        return 1e6 * this.millisecond()
    }),
    L("millisecond", "ms"),
    A("millisecond", 16),
    ce("S", ie, J),
    ce("SS", ie, Q),
    ce("SSS", ie, X),
    fn = "SSSS"; fn.length <= 9; fn += "S")
        ce(fn, oe);
    function yn(e, t) {
        t[Se] = Z(1e3 * ("0." + e))
    }
    for (fn = "S"; fn.length <= 9; fn += "S")
        _e(fn, yn);
    mn = z("Milliseconds", !1),
    C("z", 0, 0, "zoneAbbr"),
    C("zz", 0, 0, "zoneName");
    var gn = S.prototype;
    function wn(e) {
        return e
    }
    gn.add = qt,
    gn.calendar = function(e, t) {
        1 === arguments.length && (Qt(arguments[0]) ? (e = arguments[0],
        t = void 0) : function(e) {
            for (var t = d(e) && !o(e), n = !1, s = ["sameDay", "nextDay", "lastDay", "nextWeek", "lastWeek", "sameElse"], i = 0; i < s.length; i += 1)
                n = n || v(e, s[i]);
            return t && n
        }(arguments[0]) && (t = arguments[0],
        e = void 0));
        var n = e || bt()
          , s = Lt(n, this).startOf("day")
          , i = p.calendarFormat(this, s) || "sameElse"
          , r = t && (O(t[i]) ? t[i].call(this, n) : t[i]);
        return this.format(r || this.localeData().calendar(i, this, bt(n)))
    }
    ,
    gn.clone = function() {
        return new S(this)
    }
    ,
    gn.diff = function(e, t, n) {
        var s, i, r;
        if (!this.isValid())
            return NaN;
        if (!(s = Lt(e, this)).isValid())
            return NaN;
        switch (i = 6e4 * (s.utcOffset() - this.utcOffset()),
        t = V(t)) {
        case "year":
            r = Xt(this, s) / 12;
            break;
        case "month":
            r = Xt(this, s);
            break;
        case "quarter":
            r = Xt(this, s) / 3;
            break;
        case "second":
            r = (this - s) / 1e3;
            break;
        case "minute":
            r = (this - s) / 6e4;
            break;
        case "hour":
            r = (this - s) / 36e5;
            break;
        case "day":
            r = (this - s - i) / 864e5;
            break;
        case "week":
            r = (this - s - i) / 6048e5;
            break;
        default:
            r = this - s
        }
        return n ? r : I(r)
    }
    ,
    gn.endOf = function(e) {
        var t, n;
        if (void 0 === (e = V(e)) || "millisecond" === e || !this.isValid())
            return this;
        switch (n = this._isUTC ? an : rn,
        e) {
        case "year":
            t = n(this.year() + 1, 0, 1) - 1;
            break;
        case "quarter":
            t = n(this.year(), this.month() - this.month() % 3 + 3, 1) - 1;
            break;
        case "month":
            t = n(this.year(), this.month() + 1, 1) - 1;
            break;
        case "week":
            t = n(this.year(), this.month(), this.date() - this.weekday() + 7) - 1;
            break;
        case "isoWeek":
            t = n(this.year(), this.month(), this.date() - (this.isoWeekday() - 1) + 7) - 1;
            break;
        case "day":
        case "date":
            t = n(this.year(), this.month(), this.date() + 1) - 1;
            break;
        case "hour":
            t = this._d.valueOf(),
            t += 36e5 - sn(t + (this._isUTC ? 0 : 6e4 * this.utcOffset()), 36e5) - 1;
            break;
        case "minute":
            t = this._d.valueOf(),
            t += 6e4 - sn(t, 6e4) - 1;
            break;
        case "second":
            t = this._d.valueOf(),
            t += 1e3 - sn(t, 1e3) - 1
        }
        return this._d.setTime(t),
        p.updateOffset(this, !0),
        this
    }
    ,
    gn.format = function(e) {
        e = e || (this.isUtc() ? p.defaultFormatUtc : p.defaultFormat);
        var t = U(this, e);
        return this.localeData().postformat(t)
    }
    ,
    gn.from = function(e, t) {
        return this.isValid() && (Y(e) && e.isValid() || bt(e).isValid()) ? jt({
            to: this,
            from: e
        }).locale(this.locale()).humanize(!t) : this.localeData().invalidDate()
    }
    ,
    gn.fromNow = function(e) {
        return this.from(bt(), e)
    }
    ,
    gn.to = function(e, t) {
        return this.isValid() && (Y(e) && e.isValid() || bt(e).isValid()) ? jt({
            from: this,
            to: e
        }).locale(this.locale()).humanize(!t) : this.localeData().invalidDate()
    }
    ,
    gn.toNow = function(e) {
        return this.to(bt(), e)
    }
    ,
    gn.get = function(e) {
        return O(this[e = V(e)]) ? this[e]() : this
    }
    ,
    gn.invalidAt = function() {
        return k(this).overflow
    }
    ,
    gn.isAfter = function(e, t) {
        var n = Y(e) ? e : bt(e);
        return !(!this.isValid() || !n.isValid()) && ("millisecond" === (t = V(t) || "millisecond") ? this.valueOf() > n.valueOf() : n.valueOf() < this.clone().startOf(t).valueOf())
    }
    ,
    gn.isBefore = function(e, t) {
        var n = Y(e) ? e : bt(e);
        return !(!this.isValid() || !n.isValid()) && ("millisecond" === (t = V(t) || "millisecond") ? this.valueOf() < n.valueOf() : this.clone().endOf(t).valueOf() < n.valueOf())
    }
    ,
    gn.isBetween = function(e, t, n, s) {
        var i = Y(e) ? e : bt(e)
          , r = Y(t) ? t : bt(t);
        return !!(this.isValid() && i.isValid() && r.isValid()) && ("(" === (s = s || "()")[0] ? this.isAfter(i, n) : !this.isBefore(i, n)) && (")" === s[1] ? this.isBefore(r, n) : !this.isAfter(r, n))
    }
    ,
    gn.isSame = function(e, t) {
        var n, s = Y(e) ? e : bt(e);
        return !(!this.isValid() || !s.isValid()) && ("millisecond" === (t = V(t) || "millisecond") ? this.valueOf() === s.valueOf() : (n = s.valueOf(),
        this.clone().startOf(t).valueOf() <= n && n <= this.clone().endOf(t).valueOf()))
    }
    ,
    gn.isSameOrAfter = function(e, t) {
        return this.isSame(e, t) || this.isAfter(e, t)
    }
    ,
    gn.isSameOrBefore = function(e, t) {
        return this.isSame(e, t) || this.isBefore(e, t)
    }
    ,
    gn.isValid = function() {
        return w(this)
    }
    ,
    gn.lang = en,
    gn.locale = Kt,
    gn.localeData = tn,
    gn.max = Tt,
    gn.min = xt,
    gn.parsingFlags = function() {
        return y({}, k(this))
    }
    ,
    gn.set = function(e, t) {
        if ("object" == typeof e)
            for (var n = function(e) {
                var t, n = [];
                for (t in e)
                    v(e, t) && n.push({
                        unit: t,
                        priority: E[t]
                    });
                return n.sort(function(e, t) {
                    return e.priority - t.priority
                }),
                n
            }(e = G(e)), s = 0; s < n.length; s++)
                this[n[s].unit](e[n[s].unit]);
        else if (O(this[e = V(e)]))
            return this[e](t);
        return this
    }
    ,
    gn.startOf = function(e) {
        var t, n;
        if (void 0 === (e = V(e)) || "millisecond" === e || !this.isValid())
            return this;
        switch (n = this._isUTC ? an : rn,
        e) {
        case "year":
            t = n(this.year(), 0, 1);
            break;
        case "quarter":
            t = n(this.year(), this.month() - this.month() % 3, 1);
            break;
        case "month":
            t = n(this.year(), this.month(), 1);
            break;
        case "week":
            t = n(this.year(), this.month(), this.date() - this.weekday());
            break;
        case "isoWeek":
            t = n(this.year(), this.month(), this.date() - (this.isoWeekday() - 1));
            break;
        case "day":
        case "date":
            t = n(this.year(), this.month(), this.date());
            break;
        case "hour":
            t = this._d.valueOf(),
            t -= sn(t + (this._isUTC ? 0 : 6e4 * this.utcOffset()), 36e5);
            break;
        case "minute":
            t = this._d.valueOf(),
            t -= sn(t, 6e4);
            break;
        case "second":
            t = this._d.valueOf(),
            t -= sn(t, 1e3)
        }
        return this._d.setTime(t),
        p.updateOffset(this, !0),
        this
    }
    ,
    gn.subtract = Bt,
    gn.toArray = function() {
        var e = this;
        return [e.year(), e.month(), e.date(), e.hour(), e.minute(), e.second(), e.millisecond()]
    }
    ,
    gn.toObject = function() {
        var e = this;
        return {
            years: e.year(),
            months: e.month(),
            date: e.date(),
            hours: e.hours(),
            minutes: e.minutes(),
            seconds: e.seconds(),
            milliseconds: e.milliseconds()
        }
    }
    ,
    gn.toDate = function() {
        return new Date(this.valueOf())
    }
    ,
    gn.toISOString = function(e) {
        if (!this.isValid())
            return null;
        var t = !0 !== e
          , n = t ? this.clone().utc() : this;
        return n.year() < 0 || 9999 < n.year() ? U(n, t ? "YYYYYY-MM-DD[T]HH:mm:ss.SSS[Z]" : "YYYYYY-MM-DD[T]HH:mm:ss.SSSZ") : O(Date.prototype.toISOString) ? t ? this.toDate().toISOString() : new Date(this.valueOf() + 60 * this.utcOffset() * 1e3).toISOString().replace("Z", U(n, "Z")) : U(n, t ? "YYYY-MM-DD[T]HH:mm:ss.SSS[Z]" : "YYYY-MM-DD[T]HH:mm:ss.SSSZ")
    }
    ,
    gn.inspect = function() {
        if (!this.isValid())
            return "moment.invalid(/* " + this._i + " */)";
        var e, t, n, s = "moment", i = "";
        return this.isLocal() || (s = 0 === this.utcOffset() ? "moment.utc" : "moment.parseZone",
        i = "Z"),
        e = "[" + s + '("]',
        t = 0 <= this.year() && this.year() <= 9999 ? "YYYY" : "YYYYYY",
        n = i + '[")]',
        this.format(e + t + "-MM-DD[T]HH:mm:ss.SSS" + n)
    }
    ,
    "undefined" != typeof Symbol && null != Symbol.for && (gn[Symbol.for("nodejs.util.inspect.custom")] = function() {
        return "Moment<" + this.format() + ">"
    }
    ),
    gn.toJSON = function() {
        return this.isValid() ? this.toISOString() : null
    }
    ,
    gn.toString = function() {
        return this.clone().locale("en").format("ddd MMM DD YYYY HH:mm:ss [GMT]ZZ")
    }
    ,
    gn.unix = function() {
        return Math.floor(this.valueOf() / 1e3)
    }
    ,
    gn.valueOf = function() {
        return this._d.valueOf() - 6e4 * (this._offset || 0)
    }
    ,
    gn.creationData = function() {
        return {
            input: this._i,
            format: this._f,
            locale: this._locale,
            isUTC: this._isUTC,
            strict: this._strict
        }
    }
    ,
    gn.eraName = function() {
        for (var e, t = this.localeData().eras(), n = 0, s = t.length; n < s; ++n) {
            if (e = this.startOf("day").valueOf(),
            t[n].since <= e && e <= t[n].until)
                return t[n].name;
            if (t[n].until <= e && e <= t[n].since)
                return t[n].name
        }
        return ""
    }
    ,
    gn.eraNarrow = function() {
        for (var e, t = this.localeData().eras(), n = 0, s = t.length; n < s; ++n) {
            if (e = this.startOf("day").valueOf(),
            t[n].since <= e && e <= t[n].until)
                return t[n].narrow;
            if (t[n].until <= e && e <= t[n].since)
                return t[n].narrow
        }
        return ""
    }
    ,
    gn.eraAbbr = function() {
        for (var e, t = this.localeData().eras(), n = 0, s = t.length; n < s; ++n) {
            if (e = this.startOf("day").valueOf(),
            t[n].since <= e && e <= t[n].until)
                return t[n].abbr;
            if (t[n].until <= e && e <= t[n].since)
                return t[n].abbr
        }
        return ""
    }
    ,
    gn.eraYear = function() {
        for (var e, t, n = this.localeData().eras(), s = 0, i = n.length; s < i; ++s)
            if (e = n[s].since <= n[s].until ? 1 : -1,
            t = this.startOf("day").valueOf(),
            n[s].since <= t && t <= n[s].until || n[s].until <= t && t <= n[s].since)
                return (this.year() - p(n[s].since).year()) * e + n[s].offset;
        return this.year()
    }
    ,
    gn.year = Fe,
    gn.isLeapYear = function() {
        return j(this.year())
    }
    ,
    gn.weekYear = function(e) {
        return hn.call(this, e, this.week(), this.weekday(), this.localeData()._week.dow, this.localeData()._week.doy)
    }
    ,
    gn.isoWeekYear = function(e) {
        return hn.call(this, e, this.isoWeek(), this.isoWeekday(), 1, 4)
    }
    ,
    gn.quarter = gn.quarters = function(e) {
        return null == e ? Math.ceil((this.month() + 1) / 3) : this.month(3 * (e - 1) + this.month() % 3)
    }
    ,
    gn.month = Ce,
    gn.daysInMonth = function() {
        return be(this.year(), this.month())
    }
    ,
    gn.week = gn.weeks = function(e) {
        var t = this.localeData().week(this);
        return null == e ? t : this.add(7 * (e - t), "d")
    }
    ,
    gn.isoWeek = gn.isoWeeks = function(e) {
        var t = Ee(this, 1, 4).week;
        return null == e ? t : this.add(7 * (e - t), "d")
    }
    ,
    gn.weeksInYear = function() {
        var e = this.localeData()._week;
        return Ae(this.year(), e.dow, e.doy)
    }
    ,
    gn.weeksInWeekYear = function() {
        var e = this.localeData()._week;
        return Ae(this.weekYear(), e.dow, e.doy)
    }
    ,
    gn.isoWeeksInYear = function() {
        return Ae(this.year(), 1, 4)
    }
    ,
    gn.isoWeeksInISOWeekYear = function() {
        return Ae(this.isoWeekYear(), 1, 4)
    }
    ,
    gn.date = dn,
    gn.day = gn.days = function(e) {
        if (!this.isValid())
            return null != e ? this : NaN;
        var t, n, s = this._isUTC ? this._d.getUTCDay() : this._d.getDay();
        return null != e ? (t = e,
        n = this.localeData(),
        e = "string" != typeof t ? t : isNaN(t) ? "number" == typeof (t = n.weekdaysParse(t)) ? t : null : parseInt(t, 10),
        this.add(e - s, "d")) : s
    }
    ,
    gn.weekday = function(e) {
        if (!this.isValid())
            return null != e ? this : NaN;
        var t = (this.day() + 7 - this.localeData()._week.dow) % 7;
        return null == e ? t : this.add(e - t, "d")
    }
    ,
    gn.isoWeekday = function(e) {
        if (!this.isValid())
            return null != e ? this : NaN;
        if (null == e)
            return this.day() || 7;
        var t, n, s = (t = e,
        n = this.localeData(),
        "string" == typeof t ? n.weekdaysParse(t) % 7 || 7 : isNaN(t) ? null : t);
        return this.day(this.day() % 7 ? s : s - 7)
    }
    ,
    gn.dayOfYear = function(e) {
        var t = Math.round((this.clone().startOf("day") - this.clone().startOf("year")) / 864e5) + 1;
        return null == e ? t : this.add(e - t, "d")
    }
    ,
    gn.hour = gn.hours = tt,
    gn.minute = gn.minutes = cn,
    gn.second = gn.seconds = _n,
    gn.millisecond = gn.milliseconds = mn,
    gn.utcOffset = function(e, t, n) {
        var s, i = this._offset || 0;
        if (!this.isValid())
            return null != e ? this : NaN;
        if (null == e)
            return this._isUTC ? i : Vt(this);
        if ("string" == typeof e) {
            if (null === (e = Ft(he, e)))
                return this
        } else
            Math.abs(e) < 16 && !n && (e *= 60);
        return !this._isUTC && t && (s = Vt(this)),
        this._offset = e,
        this._isUTC = !0,
        null != s && this.add(s, "m"),
        i !== e && (!t || this._changeInProgress ? $t(this, jt(e - i, "m"), 1, !1) : this._changeInProgress || (this._changeInProgress = !0,
        p.updateOffset(this, !0),
        this._changeInProgress = null)),
        this
    }
    ,
    gn.utc = function(e) {
        return this.utcOffset(0, e)
    }
    ,
    gn.local = function(e) {
        return this._isUTC && (this.utcOffset(0, e),
        this._isUTC = !1,
        e && this.subtract(Vt(this), "m")),
        this
    }
    ,
    gn.parseZone = function() {
        var e;
        return null != this._tzm ? this.utcOffset(this._tzm, !1, !0) : "string" == typeof this._i && (null != (e = Ft(le, this._i)) ? this.utcOffset(e) : this.utcOffset(0, !0)),
        this
    }
    ,
    gn.hasAlignedHourOffset = function(e) {
        return !!this.isValid() && (e = e ? bt(e).utcOffset() : 0,
        (this.utcOffset() - e) % 60 == 0)
    }
    ,
    gn.isDST = function() {
        return this.utcOffset() > this.clone().month(0).utcOffset() || this.utcOffset() > this.clone().month(5).utcOffset()
    }
    ,
    gn.isLocal = function() {
        return !!this.isValid() && !this._isUTC
    }
    ,
    gn.isUtcOffset = function() {
        return !!this.isValid() && this._isUTC
    }
    ,
    gn.isUtc = Gt,
    gn.isUTC = Gt,
    gn.zoneAbbr = function() {
        return this._isUTC ? "UTC" : ""
    }
    ,
    gn.zoneName = function() {
        return this._isUTC ? "Coordinated Universal Time" : ""
    }
    ,
    gn.dates = n("dates accessor is deprecated. Use date instead.", dn),
    gn.months = n("months accessor is deprecated. Use month instead", Ce),
    gn.years = n("years accessor is deprecated. Use year instead", Fe),
    gn.zone = n("moment().zone is deprecated, use moment().utcOffset instead. http://momentjs.com/guides/#/warnings/zone/", function(e, t) {
        return null != e ? ("string" != typeof e && (e = -e),
        this.utcOffset(e, t),
        this) : -this.utcOffset()
    }),
    gn.isDSTShifted = n("isDSTShifted is deprecated. See http://momentjs.com/guides/#/warnings/dst-shifted/ for more information", function() {
        if (!c(this._isDSTShifted))
            return this._isDSTShifted;
        var e, t = {};
        return D(t, this),
        (t = Yt(t))._a ? (e = (t._isUTC ? g : bt)(t._a),
        this._isDSTShifted = this.isValid() && 0 < function(e, t) {
            for (var n = Math.min(e.length, t.length), s = Math.abs(e.length - t.length), i = 0, r = 0; r < n; r++)
                Z(e[r]) !== Z(t[r]) && i++;
            return i + s
        }(t._a, e.toArray())) : this._isDSTShifted = !1,
        this._isDSTShifted
    });
    var pn = x.prototype;
    function vn(e, t, n, s) {
        var i = ht()
          , r = g().set(s, t);
        return i[n](r, e)
    }
    function kn(e, t, n) {
        if (f(e) && (t = e,
        e = void 0),
        e = e || "",
        null != t)
            return vn(e, t, n, "month");
        for (var s = [], i = 0; i < 12; i++)
            s[i] = vn(e, i, n, "month");
        return s
    }
    function Mn(e, t, n, s) {
        "boolean" == typeof e ? f(t) && (n = t,
        t = void 0) : (t = e,
        e = !1,
        f(n = t) && (n = t,
        t = void 0)),
        t = t || "";
        var i, r = ht(), a = e ? r._week.dow : 0, o = [];
        if (null != n)
            return vn(t, (n + a) % 7, s, "day");
        for (i = 0; i < 7; i++)
            o[i] = vn(t, (i + a) % 7, s, "day");
        return o
    }
    pn.calendar = function(e, t, n) {
        var s = this._calendar[e] || this._calendar.sameElse;
        return O(s) ? s.call(t, n) : s
    }
    ,
    pn.longDateFormat = function(e) {
        var t = this._longDateFormat[e]
          , n = this._longDateFormat[e.toUpperCase()];
        return t || !n ? t : (this._longDateFormat[e] = n.match(N).map(function(e) {
            return "MMMM" === e || "MM" === e || "DD" === e || "dddd" === e ? e.slice(1) : e
        }).join(""),
        this._longDateFormat[e])
    }
    ,
    pn.invalidDate = function() {
        return this._invalidDate
    }
    ,
    pn.ordinal = function(e) {
        return this._ordinal.replace("%d", e)
    }
    ,
    pn.preparse = wn,
    pn.postformat = wn,
    pn.relativeTime = function(e, t, n, s) {
        var i = this._relativeTime[n];
        return O(i) ? i(e, t, n, s) : i.replace(/%d/i, e)
    }
    ,
    pn.pastFuture = function(e, t) {
        var n = this._relativeTime[0 < e ? "future" : "past"];
        return O(n) ? n(t) : n.replace(/%s/i, t)
    }
    ,
    pn.set = function(e) {
        var t, n;
        for (n in e)
            v(e, n) && (O(t = e[n]) ? this[n] = t : this["_" + n] = t);
        this._config = e,
        this._dayOfMonthOrdinalParseLenient = new RegExp((this._dayOfMonthOrdinalParse.source || this._ordinalParse.source) + "|" + /\d{1,2}/.source)
    }
    ,
    pn.eras = function(e, t) {
        for (var n, s = this._eras || ht("en")._eras, i = 0, r = s.length; i < r; ++i) {
            switch (typeof s[i].since) {
            case "string":
                n = p(s[i].since).startOf("day"),
                s[i].since = n.valueOf()
            }
            switch (typeof s[i].until) {
            case "undefined":
                s[i].until = 1 / 0;
                break;
            case "string":
                n = p(s[i].until).startOf("day").valueOf(),
                s[i].until = n.valueOf()
            }
        }
        return s
    }
    ,
    pn.erasParse = function(e, t, n) {
        var s, i, r, a, o, u = this.eras();
        for (e = e.toUpperCase(),
        s = 0,
        i = u.length; s < i; ++s)
            if (r = u[s].name.toUpperCase(),
            a = u[s].abbr.toUpperCase(),
            o = u[s].narrow.toUpperCase(),
            n)
                switch (t) {
                case "N":
                case "NN":
                case "NNN":
                    if (a === e)
                        return u[s];
                    break;
                case "NNNN":
                    if (r === e)
                        return u[s];
                    break;
                case "NNNNN":
                    if (o === e)
                        return u[s]
                }
            else if (0 <= [r, a, o].indexOf(e))
                return u[s]
    }
    ,
    pn.erasConvertYear = function(e, t) {
        var n = e.since <= e.until ? 1 : -1;
        return void 0 === t ? p(e.since).year() : p(e.since).year() + (t - e.offset) * n
    }
    ,
    pn.erasAbbrRegex = function(e) {
        return v(this, "_erasAbbrRegex") || un.call(this),
        e ? this._erasAbbrRegex : this._erasRegex
    }
    ,
    pn.erasNameRegex = function(e) {
        return v(this, "_erasNameRegex") || un.call(this),
        e ? this._erasNameRegex : this._erasRegex
    }
    ,
    pn.erasNarrowRegex = function(e) {
        return v(this, "_erasNarrowRegex") || un.call(this),
        e ? this._erasNarrowRegex : this._erasRegex
    }
    ,
    pn.months = function(e, t) {
        return e ? h(this._months) ? this._months[e.month()] : this._months[(this._months.isFormat || Ne).test(t) ? "format" : "standalone"][e.month()] : h(this._months) ? this._months : this._months.standalone
    }
    ,
    pn.monthsShort = function(e, t) {
        return e ? h(this._monthsShort) ? this._monthsShort[e.month()] : this._monthsShort[Ne.test(t) ? "format" : "standalone"][e.month()] : h(this._monthsShort) ? this._monthsShort : this._monthsShort.standalone
    }
    ,
    pn.monthsParse = function(e, t, n) {
        var s, i, r;
        if (this._monthsParseExact)
            return function(e, t, n) {
                var s, i, r, a = e.toLocaleLowerCase();
                if (!this._monthsParse)
                    for (this._monthsParse = [],
                    this._longMonthsParse = [],
                    this._shortMonthsParse = [],
                    s = 0; s < 12; ++s)
                        r = g([2e3, s]),
                        this._shortMonthsParse[s] = this.monthsShort(r, "").toLocaleLowerCase(),
                        this._longMonthsParse[s] = this.months(r, "").toLocaleLowerCase();
                return n ? "MMM" === t ? -1 !== (i = ge.call(this._shortMonthsParse, a)) ? i : null : -1 !== (i = ge.call(this._longMonthsParse, a)) ? i : null : "MMM" === t ? -1 !== (i = ge.call(this._shortMonthsParse, a)) || -1 !== (i = ge.call(this._longMonthsParse, a)) ? i : null : -1 !== (i = ge.call(this._longMonthsParse, a)) || -1 !== (i = ge.call(this._shortMonthsParse, a)) ? i : null
            }
            .call(this, e, t, n);
        for (this._monthsParse || (this._monthsParse = [],
        this._longMonthsParse = [],
        this._shortMonthsParse = []),
        s = 0; s < 12; s++) {
            if (i = g([2e3, s]),
            n && !this._longMonthsParse[s] && (this._longMonthsParse[s] = new RegExp("^" + this.months(i, "").replace(".", "") + "$","i"),
            this._shortMonthsParse[s] = new RegExp("^" + this.monthsShort(i, "").replace(".", "") + "$","i")),
            n || this._monthsParse[s] || (r = "^" + this.months(i, "") + "|^" + this.monthsShort(i, ""),
            this._monthsParse[s] = new RegExp(r.replace(".", ""),"i")),
            n && "MMMM" === t && this._longMonthsParse[s].test(e))
                return s;
            if (n && "MMM" === t && this._shortMonthsParse[s].test(e))
                return s;
            if (!n && this._monthsParse[s].test(e))
                return s
        }
    }
    ,
    pn.monthsRegex = function(e) {
        return this._monthsParseExact ? (v(this, "_monthsRegex") || Ue.call(this),
        e ? this._monthsStrictRegex : this._monthsRegex) : (v(this, "_monthsRegex") || (this._monthsRegex = Re),
        this._monthsStrictRegex && e ? this._monthsStrictRegex : this._monthsRegex)
    }
    ,
    pn.monthsShortRegex = function(e) {
        return this._monthsParseExact ? (v(this, "_monthsRegex") || Ue.call(this),
        e ? this._monthsShortStrictRegex : this._monthsShortRegex) : (v(this, "_monthsShortRegex") || (this._monthsShortRegex = Pe),
        this._monthsShortStrictRegex && e ? this._monthsShortStrictRegex : this._monthsShortRegex)
    }
    ,
    pn.week = function(e) {
        return Ee(e, this._week.dow, this._week.doy).week
    }
    ,
    pn.firstDayOfYear = function() {
        return this._week.doy
    }
    ,
    pn.firstDayOfWeek = function() {
        return this._week.dow
    }
    ,
    pn.weekdays = function(e, t) {
        var n = h(this._weekdays) ? this._weekdays : this._weekdays[e && !0 !== e && this._weekdays.isFormat.test(t) ? "format" : "standalone"];
        return !0 === e ? je(n, this._week.dow) : e ? n[e.day()] : n
    }
    ,
    pn.weekdaysMin = function(e) {
        return !0 === e ? je(this._weekdaysMin, this._week.dow) : e ? this._weekdaysMin[e.day()] : this._weekdaysMin
    }
    ,
    pn.weekdaysShort = function(e) {
        return !0 === e ? je(this._weekdaysShort, this._week.dow) : e ? this._weekdaysShort[e.day()] : this._weekdaysShort
    }
    ,
    pn.weekdaysParse = function(e, t, n) {
        var s, i, r;
        if (this._weekdaysParseExact)
            return function(e, t, n) {
                var s, i, r, a = e.toLocaleLowerCase();
                if (!this._weekdaysParse)
                    for (this._weekdaysParse = [],
                    this._shortWeekdaysParse = [],
                    this._minWeekdaysParse = [],
                    s = 0; s < 7; ++s)
                        r = g([2e3, 1]).day(s),
                        this._minWeekdaysParse[s] = this.weekdaysMin(r, "").toLocaleLowerCase(),
                        this._shortWeekdaysParse[s] = this.weekdaysShort(r, "").toLocaleLowerCase(),
                        this._weekdaysParse[s] = this.weekdays(r, "").toLocaleLowerCase();
                return n ? "dddd" === t ? -1 !== (i = ge.call(this._weekdaysParse, a)) ? i : null : "ddd" === t ? -1 !== (i = ge.call(this._shortWeekdaysParse, a)) ? i : null : -1 !== (i = ge.call(this._minWeekdaysParse, a)) ? i : null : "dddd" === t ? -1 !== (i = ge.call(this._weekdaysParse, a)) || -1 !== (i = ge.call(this._shortWeekdaysParse, a)) || -1 !== (i = ge.call(this._minWeekdaysParse, a)) ? i : null : "ddd" === t ? -1 !== (i = ge.call(this._shortWeekdaysParse, a)) || -1 !== (i = ge.call(this._weekdaysParse, a)) || -1 !== (i = ge.call(this._minWeekdaysParse, a)) ? i : null : -1 !== (i = ge.call(this._minWeekdaysParse, a)) || -1 !== (i = ge.call(this._weekdaysParse, a)) || -1 !== (i = ge.call(this._shortWeekdaysParse, a)) ? i : null
            }
            .call(this, e, t, n);
        for (this._weekdaysParse || (this._weekdaysParse = [],
        this._minWeekdaysParse = [],
        this._shortWeekdaysParse = [],
        this._fullWeekdaysParse = []),
        s = 0; s < 7; s++) {
            if (i = g([2e3, 1]).day(s),
            n && !this._fullWeekdaysParse[s] && (this._fullWeekdaysParse[s] = new RegExp("^" + this.weekdays(i, "").replace(".", "\\.?") + "$","i"),
            this._shortWeekdaysParse[s] = new RegExp("^" + this.weekdaysShort(i, "").replace(".", "\\.?") + "$","i"),
            this._minWeekdaysParse[s] = new RegExp("^" + this.weekdaysMin(i, "").replace(".", "\\.?") + "$","i")),
            this._weekdaysParse[s] || (r = "^" + this.weekdays(i, "") + "|^" + this.weekdaysShort(i, "") + "|^" + this.weekdaysMin(i, ""),
            this._weekdaysParse[s] = new RegExp(r.replace(".", ""),"i")),
            n && "dddd" === t && this._fullWeekdaysParse[s].test(e))
                return s;
            if (n && "ddd" === t && this._shortWeekdaysParse[s].test(e))
                return s;
            if (n && "dd" === t && this._minWeekdaysParse[s].test(e))
                return s;
            if (!n && this._weekdaysParse[s].test(e))
                return s
        }
    }
    ,
    pn.weekdaysRegex = function(e) {
        return this._weekdaysParseExact ? (v(this, "_weekdaysRegex") || Je.call(this),
        e ? this._weekdaysStrictRegex : this._weekdaysRegex) : (v(this, "_weekdaysRegex") || (this._weekdaysRegex = $e),
        this._weekdaysStrictRegex && e ? this._weekdaysStrictRegex : this._weekdaysRegex)
    }
    ,
    pn.weekdaysShortRegex = function(e) {
        return this._weekdaysParseExact ? (v(this, "_weekdaysRegex") || Je.call(this),
        e ? this._weekdaysShortStrictRegex : this._weekdaysShortRegex) : (v(this, "_weekdaysShortRegex") || (this._weekdaysShortRegex = qe),
        this._weekdaysShortStrictRegex && e ? this._weekdaysShortStrictRegex : this._weekdaysShortRegex)
    }
    ,
    pn.weekdaysMinRegex = function(e) {
        return this._weekdaysParseExact ? (v(this, "_weekdaysRegex") || Je.call(this),
        e ? this._weekdaysMinStrictRegex : this._weekdaysMinRegex) : (v(this, "_weekdaysMinRegex") || (this._weekdaysMinRegex = Be),
        this._weekdaysMinStrictRegex && e ? this._weekdaysMinStrictRegex : this._weekdaysMinRegex)
    }
    ,
    pn.isPM = function(e) {
        return "p" === (e + "").toLowerCase().charAt(0)
    }
    ,
    pn.meridiem = function(e, t, n) {
        return 11 < e ? n ? "pm" : "PM" : n ? "am" : "AM"
    }
    ,
    ut("en", {
        eras: [{
            since: "0001-01-01",
            until: 1 / 0,
            offset: 1,
            name: "Anno Domini",
            narrow: "AD",
            abbr: "AD"
        }, {
            since: "0000-12-31",
            until: -1 / 0,
            offset: 1,
            name: "Before Christ",
            narrow: "BC",
            abbr: "BC"
        }],
        dayOfMonthOrdinalParse: /\d{1,2}(th|st|nd|rd)/,
        ordinal: function(e) {
            var t = e % 10;
            return e + (1 === Z(e % 100 / 10) ? "th" : 1 == t ? "st" : 2 == t ? "nd" : 3 == t ? "rd" : "th")
        }
    }),
    p.lang = n("moment.lang is deprecated. Use moment.locale instead.", ut),
    p.langData = n("moment.langData is deprecated. Use moment.localeData instead.", ht);
    var Dn = Math.abs;
    function Sn(e, t, n, s) {
        var i = jt(t, n);
        return e._milliseconds += s * i._milliseconds,
        e._days += s * i._days,
        e._months += s * i._months,
        e._bubble()
    }
    function Yn(e) {
        return e < 0 ? Math.floor(e) : Math.ceil(e)
    }
    function On(e) {
        return 4800 * e / 146097
    }
    function bn(e) {
        return 146097 * e / 4800
    }
    function xn(e) {
        return function() {
            return this.as(e)
        }
    }
    var Tn = xn("ms")
      , Nn = xn("s")
      , Pn = xn("m")
      , Rn = xn("h")
      , Wn = xn("d")
      , Cn = xn("w")
      , Un = xn("M")
      , Hn = xn("Q")
      , Fn = xn("y");
    function Ln(e) {
        return function() {
            return this.isValid() ? this._data[e] : NaN
        }
    }
    var Vn = Ln("milliseconds")
      , Gn = Ln("seconds")
      , En = Ln("minutes")
      , An = Ln("hours")
      , jn = Ln("days")
      , In = Ln("months")
      , Zn = Ln("years")
      , zn = Math.round
      , $n = {
        ss: 44,
        s: 45,
        m: 45,
        h: 22,
        d: 26,
        w: null,
        M: 11
    };
    var qn = Math.abs;
    function Bn(e) {
        return (0 < e) - (e < 0) || +e
    }
    function Jn() {
        if (!this.isValid())
            return this.localeData().invalidDate();
        var e, t, n, s, i, r, a, o, u = qn(this._milliseconds) / 1e3, l = qn(this._days), h = qn(this._months), d = this.asSeconds();
        return d ? (e = I(u / 60),
        t = I(e / 60),
        u %= 60,
        e %= 60,
        n = I(h / 12),
        h %= 12,
        s = u ? u.toFixed(3).replace(/\.?0+$/, "") : "",
        i = d < 0 ? "-" : "",
        r = Bn(this._months) !== Bn(d) ? "-" : "",
        a = Bn(this._days) !== Bn(d) ? "-" : "",
        o = Bn(this._milliseconds) !== Bn(d) ? "-" : "",
        i + "P" + (n ? r + n + "Y" : "") + (h ? r + h + "M" : "") + (l ? a + l + "D" : "") + (t || e || u ? "T" : "") + (t ? o + t + "H" : "") + (e ? o + e + "M" : "") + (u ? o + s + "S" : "")) : "P0D"
    }
    var Qn = Rt.prototype;
    return Qn.isValid = function() {
        return this._isValid
    }
    ,
    Qn.abs = function() {
        var e = this._data;
        return this._milliseconds = Dn(this._milliseconds),
        this._days = Dn(this._days),
        this._months = Dn(this._months),
        e.milliseconds = Dn(e.milliseconds),
        e.seconds = Dn(e.seconds),
        e.minutes = Dn(e.minutes),
        e.hours = Dn(e.hours),
        e.months = Dn(e.months),
        e.years = Dn(e.years),
        this
    }
    ,
    Qn.add = function(e, t) {
        return Sn(this, e, t, 1)
    }
    ,
    Qn.subtract = function(e, t) {
        return Sn(this, e, t, -1)
    }
    ,
    Qn.as = function(e) {
        if (!this.isValid())
            return NaN;
        var t, n, s = this._milliseconds;
        if ("month" === (e = V(e)) || "quarter" === e || "year" === e)
            switch (t = this._days + s / 864e5,
            n = this._months + On(t),
            e) {
            case "month":
                return n;
            case "quarter":
                return n / 3;
            case "year":
                return n / 12
            }
        else
            switch (t = this._days + Math.round(bn(this._months)),
            e) {
            case "week":
                return t / 7 + s / 6048e5;
            case "day":
                return t + s / 864e5;
            case "hour":
                return 24 * t + s / 36e5;
            case "minute":
                return 1440 * t + s / 6e4;
            case "second":
                return 86400 * t + s / 1e3;
            case "millisecond":
                return Math.floor(864e5 * t) + s;
            default:
                throw new Error("Unknown unit " + e)
            }
    }
    ,
    Qn.asMilliseconds = Tn,
    Qn.asSeconds = Nn,
    Qn.asMinutes = Pn,
    Qn.asHours = Rn,
    Qn.asDays = Wn,
    Qn.asWeeks = Cn,
    Qn.asMonths = Un,
    Qn.asQuarters = Hn,
    Qn.asYears = Fn,
    Qn.valueOf = function() {
        return this.isValid() ? this._milliseconds + 864e5 * this._days + this._months % 12 * 2592e6 + 31536e6 * Z(this._months / 12) : NaN
    }
    ,
    Qn._bubble = function() {
        var e, t, n, s, i, r = this._milliseconds, a = this._days, o = this._months, u = this._data;
        return 0 <= r && 0 <= a && 0 <= o || r <= 0 && a <= 0 && o <= 0 || (r += 864e5 * Yn(bn(o) + a),
        o = a = 0),
        u.milliseconds = r % 1e3,
        e = I(r / 1e3),
        u.seconds = e % 60,
        t = I(e / 60),
        u.minutes = t % 60,
        n = I(t / 60),
        u.hours = n % 24,
        a += I(n / 24),
        o += i = I(On(a)),
        a -= Yn(bn(i)),
        s = I(o / 12),
        o %= 12,
        u.days = a,
        u.months = o,
        u.years = s,
        this
    }
    ,
    Qn.clone = function() {
        return jt(this)
    }
    ,
    Qn.get = function(e) {
        return e = V(e),
        this.isValid() ? this[e + "s"]() : NaN
    }
    ,
    Qn.milliseconds = Vn,
    Qn.seconds = Gn,
    Qn.minutes = En,
    Qn.hours = An,
    Qn.days = jn,
    Qn.weeks = function() {
        return I(this.days() / 7)
    }
    ,
    Qn.months = In,
    Qn.years = Zn,
    Qn.humanize = function(e, t) {
        if (!this.isValid())
            return this.localeData().invalidDate();
        var n, s, i, r, a, o, u, l, h, d, c, f, m, _, y, g = !1, w = $n;
        return "object" == typeof e && (t = e,
        e = !1),
        "boolean" == typeof e && (g = e),
        "object" == typeof t && (w = Object.assign({}, $n, t),
        null != t.s && null == t.ss && (w.ss = t.s - 1)),
        n = this.localeData(),
        r = !g,
        a = w,
        o = n,
        u = jt(i = this).abs(),
        l = zn(u.as("s")),
        h = zn(u.as("m")),
        d = zn(u.as("h")),
        c = zn(u.as("d")),
        f = zn(u.as("M")),
        m = zn(u.as("w")),
        _ = zn(u.as("y")),
        y = (l <= a.ss ? ["s", l] : l < a.s && ["ss", l]) || h <= 1 && ["m"] || h < a.m && ["mm", h] || d <= 1 && ["h"] || d < a.h && ["hh", d] || c <= 1 && ["d"] || c < a.d && ["dd", c],
        null != a.w && (y = y || m <= 1 && ["w"] || m < a.w && ["ww", m]),
        (y = y || f <= 1 && ["M"] || f < a.M && ["MM", f] || _ <= 1 && ["y"] || ["yy", _])[2] = r,
        y[3] = 0 < +i,
        y[4] = o,
        s = function(e, t, n, s, i) {
            return i.relativeTime(t || 1, !!n, e, s)
        }
        .apply(null, y),
        g && (s = n.pastFuture(+this, s)),
        n.postformat(s)
    }
    ,
    Qn.toISOString = Jn,
    Qn.toString = Jn,
    Qn.toJSON = Jn,
    Qn.locale = Kt,
    Qn.localeData = tn,
    Qn.toIsoString = n("toIsoString() is deprecated. Please use toISOString() instead (notice the capitals)", Jn),
    Qn.lang = en,
    C("X", 0, 0, "unix"),
    C("x", 0, 0, "valueOf"),
    ce("x", ue),
    ce("X", /[+-]?\d+(\.\d{1,3})?/),
    _e("X", function(e, t, n) {
        n._d = new Date(1e3 * parseFloat(e))
    }),
    _e("x", function(e, t, n) {
        n._d = new Date(Z(e))
    }),
    p.version = "2.25.3",
    e = bt,
    p.fn = gn,
    p.min = function() {
        return Nt("isBefore", [].slice.call(arguments, 0))
    }
    ,
    p.max = function() {
        return Nt("isAfter", [].slice.call(arguments, 0))
    }
    ,
    p.now = function() {
        return Date.now ? Date.now() : +new Date
    }
    ,
    p.utc = g,
    p.unix = function(e) {
        return bt(1e3 * e)
    }
    ,
    p.months = function(e, t) {
        return kn(e, t, "months")
    }
    ,
    p.isDate = m,
    p.locale = ut,
    p.invalid = M,
    p.duration = jt,
    p.isMoment = Y,
    p.weekdays = function(e, t, n) {
        return Mn(e, t, n, "weekdays")
    }
    ,
    p.parseZone = function() {
        return bt.apply(null, arguments).parseZone()
    }
    ,
    p.localeData = ht,
    p.isDuration = Wt,
    p.monthsShort = function(e, t) {
        return kn(e, t, "monthsShort")
    }
    ,
    p.weekdaysMin = function(e, t, n) {
        return Mn(e, t, n, "weekdaysMin")
    }
    ,
    p.defineLocale = lt,
    p.updateLocale = function(e, t) {
        var n, s, i;
        return null != t ? (i = nt,
        null != st[e] && null != st[e].parentLocale ? st[e].set(b(st[e]._config, t)) : (null != (s = ot(e)) && (i = s._config),
        t = b(i, t),
        null == s && (t.abbr = e),
        (n = new x(t)).parentLocale = st[e],
        st[e] = n),
        ut(e)) : null != st[e] && (null != st[e].parentLocale ? (st[e] = st[e].parentLocale,
        e === ut() && ut(e)) : null != st[e] && delete st[e]),
        st[e]
    }
    ,
    p.locales = function() {
        return s(st)
    }
    ,
    p.weekdaysShort = function(e, t, n) {
        return Mn(e, t, n, "weekdaysShort")
    }
    ,
    p.normalizeUnits = V,
    p.relativeTimeRounding = function(e) {
        return void 0 === e ? zn : "function" == typeof e && (zn = e,
        !0)
    }
    ,
    p.relativeTimeThreshold = function(e, t) {
        return void 0 !== $n[e] && (void 0 === t ? $n[e] : ($n[e] = t,
        "s" === e && ($n.ss = t - 1),
        !0))
    }
    ,
    p.calendarFormat = function(e, t) {
        var n = e.diff(t, "days", !0);
        return n < -6 ? "sameElse" : n < -1 ? "lastWeek" : n < 0 ? "lastDay" : n < 1 ? "sameDay" : n < 2 ? "nextDay" : n < 7 ? "nextWeek" : "sameElse"
    }
    ,
    p.prototype = gn,
    p.HTML5_FMT = {
        DATETIME_LOCAL: "YYYY-MM-DDTHH:mm",
        DATETIME_LOCAL_SECONDS: "YYYY-MM-DDTHH:mm:ss",
        DATETIME_LOCAL_MS: "YYYY-MM-DDTHH:mm:ss.SSS",
        DATE: "YYYY-MM-DD",
        TIME: "HH:mm",
        TIME_SECONDS: "HH:mm:ss",
        TIME_MS: "HH:mm:ss.SSS",
        WEEK: "GGGG-[W]WW",
        MONTH: "YYYY-MM"
    },
    p
});

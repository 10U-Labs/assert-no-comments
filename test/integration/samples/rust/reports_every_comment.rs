#!/usr/bin/env rust-script
#![allow(dead_code)]
//! inner line doc
/*! inner block doc */
/// outer line doc
/** outer block doc */
fn f() -> &'static str {
    let s = "// not a comment"; // trailing
    let r = r#"/* not a comment */"#;
    let c = '/';
    /* outer /* nested */ still outer */
    macro_rules! m { () => { 1 /* in macro */ }; }
    // plain
    s
}

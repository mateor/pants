// coding=utf-8
// Copyright 2015 Pants project contributors (see CONTRIBUTORS.md).
// Licensed under the Apache License, Version 2.0 (see LICENSE).

package com.pants.examples.helloLibrary;

import android.content.res.Resources;
import android.os.Bundle;
import android.support.v4.app.Fragment;
import android.widget.TextView;

public class HelloLibrary extends Fragment {

  @Override
  public void onCreate(Bundle savedInstanceState) {
    super.onCreate(savedInstanceState);

    TextView textView = new TextView(this);

    String text = getResources().getString(R.string.hello);
    textView.setText(text);

    // Toy demonstration of using an android_library comprised of a jar and associated resources.
    String greeting = getResources().getString(R.string.library_greeting)
    textView.setText(greeting);

    setContentView(textView);
  }
}
